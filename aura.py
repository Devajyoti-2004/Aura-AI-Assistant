"""Aura: a safety-conscious voice-enabled desktop assistant for Windows."""
from __future__ import annotations

import datetime as _dt
import os
import platform
import re
import subprocess
import threading
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from urllib.parse import quote_plus

APP_NAME = "Aura"
IS_WINDOWS = platform.system() == "Windows"

try:
    import pyttsx3  # type: ignore
except Exception:
    pyttsx3 = None

try:
    import speech_recognition as sr  # type: ignore
except Exception:
    sr = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class AuraApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Aura • Desktop Assistant")
        self.root.geometry("820x620")
        self.root.minsize(680, 500)
        self.root.configure(bg="#0b1020")
        self.engine = None
        self._speech_lock = threading.Lock()
        self._ai_lock = threading.Lock()
        self.ai_history: list[dict[str, str]] = []
        self.wake_stop = threading.Event()
        self.wake_thread: threading.Thread | None = None
        self.wake_active = False
        if pyttsx3:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 178)
            except Exception:
                self.engine = None
        self._build_ui()
        self.log("Aura is ready. Type a command or use the microphone button.")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        header = tk.Frame(self.root, bg="#0b1020")
        header.pack(fill="x", padx=24, pady=(22, 8))
        tk.Label(header, text="AURA", font=("Segoe UI", 25, "bold"),
                 fg="#8be9fd", bg="#0b1020").pack(anchor="w")
        tk.Label(header, text="Your desktop, at your command.",
                 font=("Segoe UI", 11), fg="#b7c4df", bg="#0b1020").pack(anchor="w", pady=(2, 0))

        card = tk.Frame(self.root, bg="#141c31", highlightthickness=1, highlightbackground="#263653")
        card.pack(fill="both", expand=True, padx=24, pady=12)
        tk.Label(card, text="ACTIVITY", font=("Segoe UI", 9, "bold"),
                 fg="#8be9fd", bg="#141c31").pack(anchor="w", padx=16, pady=(14, 5))
        self.output = scrolledtext.ScrolledText(
            card, height=15, wrap="word", state="disabled",
            bg="#0e1527", fg="#e5edff", insertbackground="white",
            font=("Consolas", 10), relief="flat", padx=12, pady=10
        )
        self.output.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        bottom = tk.Frame(self.root, bg="#0b1020")
        bottom.pack(fill="x", padx=24, pady=(0, 22))
        self.command_var = tk.StringVar()
        entry = tk.Entry(bottom, textvariable=self.command_var, font=("Segoe UI", 12),
                         bg="#141c31", fg="#ffffff", insertbackground="white",
                         relief="flat", highlightthickness=1, highlightbackground="#263653")
        entry.pack(side="left", fill="x", expand=True, ipady=12, padx=(0, 8))
        entry.bind("<Return>", lambda _event: self.submit())
        ttk.Button(bottom, text="Run command", command=self.submit).pack(side="left", padx=(0, 8))
        ttk.Button(bottom, text="🎙 Speak", command=self.listen).pack(side="left", padx=(0, 8))
        self.wake_button = ttk.Button(bottom, text="Start Wake Word", command=self.toggle_wake_word)
        self.wake_button.pack(side="left")
        entry.focus_set()

    def log(self, message: str, speaker: str = "Aura") -> None:
        # Tk widgets must only be touched by the UI thread.
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, lambda m=message, s=speaker: self.log(m, s))
            return
        stamp = _dt.datetime.now().strftime("%H:%M:%S")
        self.output.configure(state="normal")
        self.output.insert("end", f"[{stamp}] {speaker}: {message}\\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def say(self, message: str) -> None:
        self.log(message)
        if self.engine:
            def speak() -> None:
                # pyttsx3 engines are not safe for concurrent runAndWait calls.
                with self._speech_lock:
                    try:
                        self.engine.say(message)
                        self.engine.runAndWait()
                    except Exception:
                        pass
            threading.Thread(target=speak, daemon=True).start()

    def submit(self) -> None:
        command = self.command_var.get().strip()
        if not command:
            return
        self.command_var.set("")
        self.log(command, "You")
        threading.Thread(target=self.handle_command, args=(command,), daemon=True).start()

    def listen(self) -> None:
        if not sr:
            messagebox.showinfo("Voice input unavailable",
                                "Install SpeechRecognition and a compatible PyAudio build, then restart Aura. You can still type commands.")
            return
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def toggle_wake_word(self) -> None:
        if not sr:
            messagebox.showinfo(
                "Voice input unavailable",
                "Install SpeechRecognition and a compatible PyAudio build before enabling the wake word."
            )
            return
        if self.wake_active:
            self.wake_stop.set()
            self.wake_active = False
            self.wake_button.configure(text="Start Wake Word")
            self.say("Wake-word listening is stopping.")
            return
        self.wake_stop.clear()
        self.wake_active = True
        self.wake_button.configure(text="Stop Wake Word")
        self.say("Wake-word listening is on. Say 'Hey Aura' to activate me.")
        self.wake_thread = threading.Thread(target=self._wake_word_worker, daemon=True)
        self.wake_thread.start()

    def _wake_word_worker(self) -> None:
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                while not self.wake_stop.is_set():
                    try:
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    except sr.WaitTimeoutError:
                        continue
                    try:
                        phrase = recognizer.recognize_google(audio).strip()
                    except Exception:
                        continue
                    normalized = phrase.lower().replace(",", " ")
                    match = re.search(r"\b(?:hey|hi|okay|ok)\s+aura\b[, ]*(.*)", normalized)
                    if not match:
                        continue
                    command = match.group(1).strip(" .,!?")
                    self.root.after(0, lambda p=phrase: self.log(p, "Wake word"))
                    if not command:
                        self.root.after(0, lambda: self.say("I'm listening. Please say your command."))
                        try:
                            follow_up = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                            command = recognizer.recognize_google(follow_up).strip()
                        except Exception:
                            self.root.after(0, lambda: self.log("I didn't catch a command. Try again."))
                            continue
                    if command:
                        self.root.after(0, lambda q=command: self.log(q, "You (voice)"))
                        self.handle_command(command)
        except Exception as exc:
            self.root.after(0, lambda e=str(exc): self.say(
                f"Wake-word listener stopped: {e}. You can still type commands or use Speak."
            ))
        finally:
            self.wake_active = False
            self.root.after(0, lambda: self.wake_button.configure(text="Start Wake Word"))

    def _listen_worker(self) -> None:
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                self.root.after(0, lambda: self.log("Listening…"))
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            # This backend may send audio to Google's speech service.
            phrase = recognizer.recognize_google(audio)
            self.root.after(0, lambda p=phrase: self.log(p, "You (voice)"))
            self.handle_command(phrase)
        except Exception as exc:
            self.root.after(0, lambda e=str(exc): self.say(f"Voice input failed: {e}"))

    def handle_command(self, raw: str) -> None:
        cmd = raw.strip()
        low = cmd.lower()

        if low in {"help", "commands", "what can you do"}:
            self.say("Try: open YouTube, open https://github.com, search web Python, find file resume, volume 35, what time is it, or lock screen.")
            return

        if re.search(r"\b(time|date)\b", low):
            now = _dt.datetime.now()
            self.say(now.strftime("It is %I:%M %p on %A, %B %d, %Y."))
            return

        if low.startswith("open "):
            target = cmd[5:].strip()
            known = {
                "youtube": "https://www.youtube.com",
                "google": "https://www.google.com",
                "github": "https://github.com",
                "gmail": "https://mail.google.com",
                "chatgpt": "https://chatgpt.com",
            }
            url = known.get(target.lower(), target)
            if not re.match(r"^https?://", url, re.I):
                # Avoid interpreting arbitrary text as a local executable.
                if "." in url and " " not in url:
                    url = "https://" + url
                else:
                    self.say("I can open known websites or a full http/https URL. Try 'open YouTube'.")
                    return
            try:
                webbrowser.open(url, new=2)
                self.say(f"Opening {target}.")
            except Exception as exc:
                self.say(f"Could not open the website: {exc}")
            return

        if low.startswith("search web "):
            query = cmd[len("search web "):].strip()
            if query:
                webbrowser.open("https://www.google.com/search?q=" + quote_plus(query), new=2)
                self.say(f"Searching the web for {query}.")
            else:
                self.say("Tell me what you want to search for.")
            return

        if low.startswith("find file "):
            query = cmd[len("find file "):].strip().lower()
            if not query:
                self.say("Give me a filename to search for.")
                return
            matches = self.find_files(query)
            if matches:
                self.say("Found: " + "; ".join(str(p) for p in matches[:8]))
            else:
                self.say("No matching files found in common user folders.")
            return

        volume_match = re.fullmatch(r"(?:set )?volume\s+(\d{1,3})", low)
        if volume_match:
            level = int(volume_match.group(1))
            if not 0 <= level <= 100:
                self.say("Volume must be between 0 and 100.")
            elif not IS_WINDOWS:
                self.say("Volume control is currently implemented for Windows only.")
            else:
                self.set_windows_volume(level)
            return

        if low in {"lock screen", "lock my computer", "lock computer"}:
            if not IS_WINDOWS:
                self.say("Lock screen is currently implemented for Windows only.")
                return
            # Confirmation dialogs must be created on Tk's UI thread.
            self.root.after(0, self._confirm_lock_screen)
            return

        if low in {"open downloads", "open documents", "open desktop"}:
            folder_name = low.replace("open ", "").title()
            folder = Path.home() / folder_name
            if folder.exists():
                try:
                    if IS_WINDOWS:
                        os.startfile(str(folder))  # type: ignore[attr-defined]
                    else:
                        webbrowser.open(folder.as_uri())
                    self.say(f"Opening your {folder_name} folder.")
                except Exception as exc:
                    self.say(f"Could not open folder: {exc}")
            else:
                self.say(f"I couldn't find {folder_name} in your home folder.")
            return

        # Natural-language questions fall back to the optional AI conversation engine.
        if OpenAI and os.environ.get("OPENAI_API_KEY", "").strip():
            self.ask_ai(cmd)
        else:
            self.say(
                "I don't know that command yet. Say 'help' for system commands. "
                "For AI conversation, install the requirements and configure OPENAI_API_KEY in a local .env file."
            )

    def ask_ai(self, prompt: str) -> None:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not OpenAI or not api_key:
            self.say("AI chat is not configured. Add OPENAI_API_KEY to your local .env file.")
            return
        model = os.environ.get("OPENAI_MODEL", "gpt-5.5").strip() or "gpt-5.5"
        try:
            with self._ai_lock:
                client = OpenAI(api_key=api_key)
                history = self.ai_history[-12:]
                response = client.responses.create(
                    model=model,
                    instructions=(
                        "You are Aura, a helpful, concise desktop assistant. "
                        "You may explain how to do tasks, but do not claim to have performed "
                        "actions on the computer unless the application explicitly did so. "
                        "Never request or reveal passwords, API keys, or other secrets."
                    ),
                    input=history + [{"role": "user", "content": prompt}],
                    max_output_tokens=500,
                )
                answer = (response.output_text or "").strip()
                if not answer:
                    answer = "I couldn't generate a response just now. Please try again."
                self.ai_history.extend([
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": answer},
                ])
                self.ai_history = self.ai_history[-12:]
            self.say(answer)
        except Exception as exc:
            self.say(f"AI request failed: {exc}. Check your API key, model setting, and internet connection.")

    def _confirm_lock_screen(self) -> None:
        if not messagebox.askyesno("Confirm lock", "Lock this computer now?"):
            self.say("Cancelled.")
            return
        try:
            subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
            self.say("Locking the screen.")
        except Exception as exc:
            self.say(f"Could not lock the screen: {exc}")

    @staticmethod
    def find_files(query: str) -> list[Path]:
        roots = [Path.home() / name for name in ("Desktop", "Documents", "Downloads")]
        results: list[Path] = []
        for root in roots:
            if not root.is_dir():
                continue
            try:
                for path in root.rglob("*"):
                    if len(results) >= 20:
                        return results
                    try:
                        if query in path.name.lower():
                            results.append(path)
                    except (PermissionError, OSError):
                        continue
            except (PermissionError, OSError):
                continue
        return results

    def set_windows_volume(self, level: int) -> None:
        # Uses Windows Core Audio via PowerShell; no downloaded scripts or external commands.
        script = (
            "$w = New-Object -ComObject WScript.Shell; "
            "$n = [Math]::Round(" + str(level) + " / 2); "
            "1..50 | ForEach-Object { $w.SendKeys([char]174) }; "
            "1..$n | ForEach-Object { $w.SendKeys([char]175) }"
        )
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", script],
                           capture_output=True, text=True, timeout=8, check=False)
            self.say(f"Requested volume adjustment to approximately {level} percent. Windows keyboard volume steps may vary.")
        except Exception as exc:
            self.say(f"Could not adjust volume: {exc}")

    def on_close(self) -> None:
        self.wake_stop.set()
        try:
            if self.engine:
                self.engine.stop()
        except Exception:
            pass
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    AuraApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
