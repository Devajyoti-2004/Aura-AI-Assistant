# Aura — Voice-Activated Desktop Assistant

Aura is a Python desktop assistant starter project for Windows. It provides a small dashboard, optional speech input/output, browser search/opening, safe file search, volume controls, and basic system actions.

## Features
- Tkinter dashboard with command input and activity log
- Optional voice recognition (microphone) and text-to-speech
- Open websites and search the web
- Search filenames in common user folders
- Set system volume on Windows (uses PowerShell / Windows audio APIs where available)
- Confirm before locking the screen or running other sensitive actions
- No arbitrary shell-command execution from natural-language input

## Setup (Windows 10/11)
1. Install Python 3.10+ from https://www.python.org/downloads/ and enable **Add Python to PATH**.
2. Clone this repository:
   ```powershell
   git clone https://github.com/Devajyoti-2004/Aura-AI-Assistant.git
   cd Aura-AI-Assistant
   ```
3. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. Start Aura:
   ```powershell
   python aura.py
   ```

## Voice setup
Voice input uses SpeechRecognition + PyAudio and may require a compatible microphone. If microphone setup fails, use the command box. Text-to-speech uses pyttsx3. The app remains usable without either optional package.

## Example commands
- `open YouTube`
- `open https://github.com`
- `search web Python voice assistant`
- `find file resume`
- `volume 35`
- `what time is it`
- `help`

## Safety and privacy
Aura does not execute arbitrary terminal commands, delete files, send messages, transfer money, or silently access private content. File search checks common user folders and returns matching paths only. Speech recognition may send audio to Google's recognition service when that backend is used; use typed commands if you prefer not to send audio to an online service.

## Project structure
- `aura.py` — desktop UI, command routing, and safe integrations
- `requirements.txt` — optional voice dependencies
- `.gitignore` — local Python environment exclusions

## License
MIT