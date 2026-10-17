# Aura — Voice-Activated Desktop Assistant

Aura is a Python desktop assistant for Windows 10/11. It has a dark Tkinter dashboard, typed commands, optional voice input and spoken replies, an opt-in **Hey Aura** wake-word listener, and optional AI conversation through the OpenAI API.

## Features

- Dark desktop dashboard with activity log
- Typed commands and one-shot microphone input
- Optional **Hey Aura** wake-word listening toggle
- Optional AI conversation with short in-session chat history
- Open common websites or a supplied HTTP/HTTPS URL
- Search the web using your default browser
- Find filenames in Desktop, Documents, and Downloads
- Approximate Windows volume adjustment using media-key events
- Confirm before locking the Windows session
- Does not execute arbitrary terminal commands from natural-language input
- Works as a typed-command app even when voice libraries or AI configuration are unavailable

## Requirements

- Windows 10/11 recommended
- Python 3.10 or newer
- Microphone for voice features (optional)
- An OpenAI API key for AI chat (optional; API usage may incur charges)

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

If PowerShell blocks environment activation, run the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe aura.py
```

## Enable AI chat (optional)

1. Copy the example configuration file to a local file named `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `.env` and set your own key and preferred API model:
   ```dotenv
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-5.5
   ```
3. Save the file and restart Aura.

Get your API key from the official [OpenAI API platform](https://platform.openai.com/api-keys). API usage may be billed separately from a ChatGPT subscription. Never share your key or commit your real `.env` file; `.env` is excluded by `.gitignore`.

When AI is configured, questions that are not recognized as built-in commands are sent to the configured model. The recent conversation context stays in memory for the current app session only.

## Example commands

Type a command in the bottom input field, click **Speak**, or enable wake-word listening and say “Hey Aura”:

- `help` — show supported command examples
- `what time is it` or `what is the date`
- `open YouTube`, `open Gmail`, `open GitHub`, `open ChatGPT`
- `open https://example.com`
- `search web Python voice assistant`
- `find file resume`
- `open Downloads`, `open Documents`, `open Desktop`
- `volume 35` — approximate volume adjustment on Windows
- `lock screen` — asks for confirmation before locking
- `Explain how neural networks learn` — AI chat when configured

## Voice setup and privacy

- Voice input requires `SpeechRecognition` and a compatible `PyAudio` installation. On some Windows/Python combinations, PyAudio installation can require a compatible wheel or compiler.
- Click **Start Wake Word** to opt into ongoing microphone listening. Click **Stop Wake Word** to stop it. Aura does not start wake-word listening automatically.
- The wake-word listener uses Google's online speech-recognition service to detect “Hey Aura”; captured speech may be sent to that service. It is not an offline/private wake-word detector. Use typed commands if you do not want to send audio to an online service.
- Text-to-speech uses `pyttsx3`. If it fails to initialize, Aura remains usable as a typed-command app.
- AI questions are sent to the OpenAI API when AI is configured. Do not submit passwords, private keys, or sensitive information.
- Volume adjustment sends Windows media-key events, so the result is approximate and may depend on the audio device and Windows configuration.

## Safety

Aura intentionally does **not** run arbitrary shell commands, delete files, send messages, transfer money, or silently access private content. File search checks common user folders and reports matching paths. Locking the screen requires confirmation.

## Development check

Run a syntax check locally:

```powershell
python -m compileall -q .
```

A GitHub Actions workflow runs this check on pushes to `main` and pull requests.

## Project structure

- `aura.py` — UI, command routing, wake-word listener, AI chat, and system actions
- `requirements.txt` — voice and AI dependencies
- `.env.example` — example local AI configuration (contains no real key)
- `.gitignore` — excludes virtual environments, local settings, and Python artifacts
- `.github/workflows/ci.yml` — basic Python syntax check

## License

MIT. See [LICENSE](LICENSE).
