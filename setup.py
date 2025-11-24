"""
NEXUS Music Manager - Setup Configuration
Project: AGENTE_MUSICA_MP3_001
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="nexus-music-manager",
    version="1.0.0",
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

    # Python version requirement
    python_requires=">=3.8",

    # Dependencies
    install_requires=[
        "PyQt6>=6.5.0",
        "google-api-python-client>=2.100.0",
        "google-auth>=2.23.0",
        "google-auth-oauthlib>=1.1.0",
        "google-auth-httplib2>=0.1.1",
        "spotipy>=2.23.0",
        "yt-dlp>=2023.10.13",
        "musicbrainzngs>=0.7.1",
        "mutagen>=1.47.0",
        "pydub>=0.25.1",
        "pygame>=2.5.0",
        "numpy>=1.24.0",
        "lyricsgenius>=3.0.1",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "keyring>=24.0.0",
    ],

    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
        ],
        "fingerprint": [
            "pyacoustid>=1.2.2",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Players",
    ],

    # Keywords for search
    keywords="music manager youtube spotify download mp3 library pyqt6",

    # Include additional files
    include_package_data=True,

    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/rrojashub-source/nexus-music-manager/issues",
        "Source": "https://github.com/rrojashub-source/nexus-music-manager",
    },
)
