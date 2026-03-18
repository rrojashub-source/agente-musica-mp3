# Building the Project

## Development Setup

```bash
# Clone and install
git clone https://github.com/rrojashub-source/agente-musica-mp3.git
cd agente-musica-mp3
pip install -r requirements.txt        # 26 production deps
pip install -r requirements-dev.txt    # 14 dev deps (pytest, mypy, black, etc.)
```

## Running

```bash
# Development
python src/main.py

# Production (Windows standalone)
dist/NEXUS_Music_Manager.exe
```

## Dependencies

**requirements.txt** (26 deps): PySide6, python-mpv, numpy, requests, spotipy, yt-dlp, musicbrainzngs, mutagen, Flask, PyJWT, cryptography, acoustid, scikit-learn, pillow, qrcode, google-api-python-client, google-auth-oauthlib, lyricsgenius, pychord, librosa (chords only), discord-rpc-py, python-dotenv.

**requirements-dev.txt** (14 deps): pytest, pytest-cov, pytest-mock, mypy, black, isort, flake8, bandit, pre-commit, types-requests, types-Flask, pyinstaller.

**setup.py** extras: `pip install .[all]` instala todo. Extras individuales: fingerprint, chords, audio-analysis, remote, visualizer, discord, dotenv.

## Building the Executable

```bash
# PyInstaller (current method)
pyinstaller nexus_music_manager.spec --clean
# Output: dist/NEXUS_Music_Manager.exe (~151MB with UPX)

# Nuitka (blocked by yt_dlp #2879)
# python -m nuitka --standalone --enable-plugin=pyside6 src/main.py
```

**Build scripts:** `scripts/` contiene 16 scripts utilitarios para build, test, y mantenimiento.

## Linters & Quality

```bash
# Pre-commit (runs automatically on git commit)
pre-commit run --all-files

# Manual
black src/ tests/                    # Formatter
isort src/ tests/                    # Import sorting
flake8 src/ tests/                   # Linter (max-line-length=120)
mypy src/ --ignore-missing-imports   # Type checking (strict mode)
bandit -r src/ -ll                   # Security scan
```

## CI/CD

GitHub Actions pipeline (`.github/workflows/ci.yml`):
- Matrix: Python 3.10-3.13
- Jobs: test (pytest + xvfb for GUI), type-check (mypy), lint (flake8), security (bandit)
- Windows build artifact
