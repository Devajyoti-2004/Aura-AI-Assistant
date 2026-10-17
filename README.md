# Aura — Voice-Activated Desktop Assistant

Aura is a lightweight Python desktop assistant for Windows 10/11. It provides a dark Tkinter dashboard, typed commands, optional voice input and spoken replies, browser actions, file search, and a small set of system controls.

## Features

- Dark desktop dashboard with an activity log
- Optional speech-to-text microphone input and text-to-speech replies
- Open common websites or a supplied HTTP/HTTPS URL
- Search the web using your default browser
- Find filenames in Desktop, Documents, and Downloads
- Approximate Windows master-volume adjustment using media-key events
- Confirm before locking the Windows session
- No arbitrary terminal-command execution from natural-language input
- Continues to work with typed commands when optional voice libraries are unavailable

## Requirements

- Windows 10 or Windows 11 recommended
- Python 3.10 or newer
- Microphone for voice input (optional)
- Internet connection for Google's speech-recognition backend and browser searches (optional)

## Install and run

Open PowerShell in the folder where you want the project:

```powershell
git clone https://github.com/Devajyoti-2004/Aura-AI-Assistant.git
cd Aura-AI-Assistant
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python aura.py
```

If PowerShell blocks environment activation, you can run the environment's Python directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe aura.py
```

## Example commands

Type a command in the bottom input field, or click **Speak**:

- `help` — show supported command examples
- `what time is it` or `what is the date`
- `open YouTube`, `open Gmail`, `open GitHub`, `open ChatGPT`
- `open https://example.com`
- `search web Python voice assistant`
- `find file resume`
- `open Downloads`, `open Documents`, `open Desktop`
- `volume 35` — approximate volume adjustment on Windows
- `lock screen` — asks for confirmation before locking

## Voice setup and troubleshooting

- Voice input requires `SpeechRecognition` and a compatible `PyAudio` installation. On some Windows/Python combinations, PyAudio installation can require a compatible wheel or compiler.
- Text-to-speech uses `pyttsx3`. If it fails to initialize, Aura remains usable as a typed-command app.
- Speech recognition uses Google's online recognition service through `recognize_google`; recorded audio may be sent to that service. Use typed commands if you do not want to send audio to an online service.
- If the microphone is unavailable or permission is denied, use the command box.
- Volume adjustment sends Windows media-key events, so the result is approximate and may depend on the audio device and Windows configuration.

## Safety and privacy

Aura intentionally does **not** run arbitrary shell commands, delete files, send messages, transfer money, or silently access private content. File search only scans common user folders and reports matching paths. Locking the screen requires confirmation. Browser searches and voice recognition may use online services as described above.

## Development check

Run a syntax check locally:

```powershell
python -m compileall -q .
```

A GitHub Actions workflow also runs this check when code is pushed or a pull request is opened.

## Project structure

- `aura.py` — UI, command routing, voice integration, and system actions
- `requirements.txt` — optional voice dependencies
- `.gitignore` — excludes virtual environments, local settings, and Python artifacts
- `.github/workflows/ci.yml` — basic Python syntax check

## License

MIT. See [LICENSE](LICENSE).
