"""Mutagen compatibility shim — tries mutagen-rs (Rust, 100-300x faster), falls back to mutagen."""

try:
    from mutagen_rs import File as MutagenFile
    from mutagen_rs import MutagenError
    from mutagen_rs.id3 import APIC, ID3, TALB, TCON, TDRC, TIT2, TPE1
    from mutagen_rs.id3 import ID3Error
    from mutagen_rs.mp3 import MP3

    BACKEND = "mutagen-rs"
except ImportError:
    from mutagen import File as MutagenFile  # type: ignore[no-redef]
    from mutagen import MutagenError  # type: ignore[no-redef]
    from mutagen.id3 import APIC, ID3, TALB, TCON, TDRC, TIT2, TPE1  # type: ignore[no-redef]
    from mutagen.id3 import error as ID3Error  # type: ignore[assignment,no-redef]
    from mutagen.mp3 import MP3  # type: ignore[no-redef]

    BACKEND = "mutagen"

__all__ = [
    "APIC",
    "BACKEND",
    "ID3",
    "ID3Error",
    "MP3",
    "MutagenError",
    "MutagenFile",
    "TALB",
    "TCON",
    "TDRC",
    "TIT2",
    "TPE1",
]
