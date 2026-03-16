"""
NEXUS Music Manager - Setup Configuration
Project: AGENTE_MUSICA_MP3_001
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="nexus-music-manager",
    version="2.1.0",
    author="Ricardo",
    author_email="",
    description="Professional Music Library Manager - YouTube downloader, Spotify search, and more",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rrojashub-source/nexus-music-manager",
    license="MIT",
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=["main"],
    # Python version requirement
    python_requires=">=3.10",
    # Dependencies
    install_requires=[
        "PySide6>=6.5.0",
        "google-api-python-client>=2.100.0",
        "google-auth>=2.23.0",
        "google-auth-oauthlib>=1.1.0",
        "google-auth-httplib2>=0.1.1",
        "spotipy>=2.23.0",
        "yt-dlp>=2023.10.13",
        "musicbrainzngs>=0.7.1",
        "mutagen>=1.47.0",
        "python-mpv>=1.0.0",
        "numpy>=1.24.0",
        "lyricsgenius>=3.0.1",
        "requests>=2.31.0",
        "keyring>=24.0.0",
    ],
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-qt>=4.2.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
            "pip-audit>=2.6.0",
            "safety>=2.3.5",
            "bandit>=1.7.5",
        ],
        "content-filter": [
            "better-profanity>=0.7.0",
        ],
        "fingerprint": [
            "pyacoustid>=1.2.2",
        ],
        "audio-analysis": [
            "pydub>=0.25.1",
        ],
        "chords": [
            "librosa>=0.10.0",
            "pychord>=1.0",
            "scipy>=1.11.0",
        ],
        "remote": [
            "flask>=3.0.0",
            "flask-cors>=4.0.0",
            "qrcode>=7.4.0",
        ],
        "visualizer": [
            "PyOpenGL>=3.1.7",
            "PyOpenGL-accelerate>=3.1.7",
        ],
        "discord": [
            "pypresence>=4.3.0",
        ],
        "dotenv": [
            "python-dotenv>=1.0.0",
        ],
        "all": [
            "pyacoustid>=1.2.2",
            "pypresence>=4.3.0",
            "flask>=3.0.0",
            "flask-cors>=4.0.0",
            "qrcode>=7.4.0",
            "PyOpenGL>=3.1.7",
            "PyOpenGL-accelerate>=3.1.7",
            "librosa>=0.10.0",
            "pychord>=1.0",
            "scipy>=1.11.0",
            "python-dotenv>=1.0.0",
            "pydub>=0.25.1",
            "better-profanity>=0.7.0",
        ],
    },
    # Entry points
    entry_points={
        "console_scripts": [
            "nexus-music=main:main",
        ],
        "gui_scripts": [
            "nexus-music-gui=main:main",
        ],
    },
    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Players",
    ],
    # Keywords for search
    keywords="music manager youtube spotify download mp3 library pyside6",
    # Include additional files
    include_package_data=True,
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/rrojashub-source/nexus-music-manager/issues",
        "Source": "https://github.com/rrojashub-source/nexus-music-manager",
    },
)
