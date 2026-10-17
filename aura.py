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


class AuraApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Aura • Desktop Assistant")
        self.root.geometry("820x620")
        self.root.minsize(680, 500)
        self.root.configure(bg="#0b1020")
        self.engine = None
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
        ttk.Button(bottom, text="🎙 Speak", command=self.listen).pack(side="left")
        entry.focus_set()

    def log(self, message: str, speaker: str = "Aura") -> None:
        stamp = _dt.datetime.now().strftime("%H:%M:%S")
        self.output.configure(state="normal")
        self.output.insert("end", f"[{stamp}] {speaker}: {message}\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def say(self, message: str) -> None:
        self.log(message)
        if self.engine:
            def speak() -> None:
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
            if messagebox.askyesno("Confirm lock", "Lock this computer now?"):
                try:
                    subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
                    self.say("Locking the screen.")
                except Exception as exc:
                    self.say(f"Could not lock the screen: {exc}")
            else:
                self.say("Cancelled.")
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

        self.say("I don't know that command yet. Say 'help' to see supported commands.")

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
