"""
Audio Equalizer - 10-Band Equalizer for NEXUS Music Manager

Provides real-time audio equalization with preset support.

Features:
- 10-band graphic equalizer (31Hz to 16kHz)
- Built-in presets (Rock, Pop, Jazz, Classical, etc.)
- Custom preset save/load
- Per-band gain adjustment (-12dB to +12dB)
- Real-time preview (when supported)

Note: pygame.mixer doesn't support real-time EQ.
This module provides UI support and preset management.
Future: Integration with audio processing pipeline.

Created: December 11, 2025
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EqualizerBand(Enum):
    """Standard 10-band equalizer frequencies"""

    BAND_31HZ = 31
    BAND_62HZ = 62
    BAND_125HZ = 125
    BAND_250HZ = 250
    BAND_500HZ = 500
    BAND_1KHZ = 1000
    BAND_2KHZ = 2000
    BAND_4KHZ = 4000
    BAND_8KHZ = 8000
    BAND_16KHZ = 16000


# Band labels for UI display
BAND_LABELS = {
    EqualizerBand.BAND_31HZ: "31",
    EqualizerBand.BAND_62HZ: "62",
    EqualizerBand.BAND_125HZ: "125",
    EqualizerBand.BAND_250HZ: "250",
    EqualizerBand.BAND_500HZ: "500",
    EqualizerBand.BAND_1KHZ: "1K",
    EqualizerBand.BAND_2KHZ: "2K",
    EqualizerBand.BAND_4KHZ: "4K",
    EqualizerBand.BAND_8KHZ: "8K",
    EqualizerBand.BAND_16KHZ: "16K",
}


@dataclass
class EqualizerPreset:
    """Equalizer preset configuration"""

    name: str
    bands: Dict[int, float] = field(default_factory=dict)  # freq -> gain in dB
    description: str = ""
    is_custom: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "bands": {str(k): v for k, v in self.bands.items()},
            "description": self.description,
            "is_custom": self.is_custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EqualizerPreset":
        """Create from dictionary"""
        bands = {int(k): v for k, v in data.get("bands", {}).items()}
        return cls(
            name=data.get("name", "Custom"),
            bands=bands,
            description=data.get("description", ""),
            is_custom=data.get("is_custom", True),
        )


# Built-in presets (gain values in dB, range -12 to +12)
BUILTIN_PRESETS = {
    "flat": EqualizerPreset(
        name="Flat",
        bands={31: 0, 62: 0, 125: 0, 250: 0, 500: 0, 1000: 0, 2000: 0, 4000: 0, 8000: 0, 16000: 0},
        description="No equalization - natural sound",
    ),
    "rock": EqualizerPreset(
        name="Rock",
        bands={31: 4, 62: 3, 125: 2, 250: 1, 500: -1, 1000: -1, 2000: 2, 4000: 3, 8000: 4, 16000: 4},
        description="Enhanced bass and treble for rock music",
    ),
    "pop": EqualizerPreset(
        name="Pop",
        bands={31: -1, 62: 1, 125: 3, 250: 4, 500: 3, 1000: 1, 2000: 0, 4000: 1, 8000: 2, 16000: 3},
        description="Bright and punchy for pop music",
    ),
    "jazz": EqualizerPreset(
        name="Jazz",
        bands={31: 2, 62: 2, 125: 1, 250: 0, 500: -1, 1000: 0, 2000: 1, 4000: 2, 8000: 2, 16000: 3},
        description="Warm with detailed highs for jazz",
    ),
    "classical": EqualizerPreset(
        name="Classical",
        bands={31: 3, 62: 2, 125: 1, 250: 0, 500: 0, 1000: 0, 2000: 0, 4000: 1, 8000: 2, 16000: 3},
        description="Natural with enhanced dynamics for classical",
    ),
    "electronic": EqualizerPreset(
        name="Electronic",
        bands={31: 5, 62: 4, 125: 3, 250: 0, 500: -2, 1000: 0, 2000: 2, 4000: 3, 8000: 4, 16000: 5},
        description="Deep bass and crisp highs for electronic",
    ),
    "hip_hop": EqualizerPreset(
        name="Hip-Hop",
        bands={31: 5, 62: 4, 125: 3, 250: 1, 500: 0, 1000: -1, 2000: 1, 4000: 2, 8000: 2, 16000: 3},
        description="Heavy bass for hip-hop and R&B",
    ),
    "bass_boost": EqualizerPreset(
        name="Bass Boost",
        bands={31: 6, 62: 5, 125: 4, 250: 2, 500: 0, 1000: 0, 2000: 0, 4000: 0, 8000: 0, 16000: 0},
        description="Maximum bass enhancement",
    ),
    "treble_boost": EqualizerPreset(
        name="Treble Boost",
        bands={31: 0, 62: 0, 125: 0, 250: 0, 500: 0, 1000: 0, 2000: 2, 4000: 3, 8000: 4, 16000: 5},
        description="Enhanced high frequencies",
    ),
    "vocal": EqualizerPreset(
        name="Vocal",
        bands={31: -2, 62: -1, 125: 0, 250: 2, 500: 4, 1000: 4, 2000: 3, 4000: 2, 8000: 1, 16000: 0},
        description="Enhanced mid frequencies for vocals",
    ),
    "acoustic": EqualizerPreset(
        name="Acoustic",
        bands={31: 2, 62: 2, 125: 1, 250: 0, 500: 1, 1000: 2, 2000: 3, 4000: 3, 8000: 2, 16000: 2},
        description="Natural warmth for acoustic instruments",
    ),
    "loudness": EqualizerPreset(
        name="Loudness",
        bands={31: 4, 62: 3, 125: 2, 250: 0, 500: -1, 1000: -1, 2000: 0, 4000: 2, 8000: 3, 16000: 4},
        description="Enhanced bass and treble for low volume listening",
    ),
}


class AudioEqualizer:
    """
    10-Band Audio Equalizer

    Manages equalizer settings and presets.

    Usage:
        eq = AudioEqualizer()

        # Apply preset
        eq.apply_preset('rock')

        # Manual band adjustment
        eq.set_band_gain(1000, 3.5)  # +3.5dB at 1kHz

        # Get current settings
        gains = eq.get_all_gains()

        # Save custom preset
        eq.save_custom_preset('my_preset', 'My custom EQ')
    """

    # Gain limits
    MIN_GAIN = -12.0  # dB
    MAX_GAIN = 12.0  # dB

    def __init__(self, config_dir: Optional[str] = None) -> None:
        """
        Initialize equalizer

        Args:
            config_dir: Directory to store custom presets (default: data/)
        """
        self._enabled: bool = True
        self._current_preset: str = "flat"
        self._custom_presets: Dict[str, EqualizerPreset] = {}

        # Current band gains (freq -> gain in dB)
        self._bands: Dict[int, float] = {band.value: 0.0 for band in EqualizerBand}

        # Config directory for custom presets
        self._config_dir: Path = Path(config_dir) if config_dir else Path("data")
        self._presets_file: Path = self._config_dir / "eq_presets.json"

        # Load custom presets
        self._load_custom_presets()

        logger.info("AudioEqualizer initialized (10-band)")

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable equalizer"""
        self._enabled = enabled
        logger.info(f"Equalizer {'enabled' if enabled else 'disabled'}")

    def is_enabled(self) -> bool:
        """Check if equalizer is enabled"""
        return self._enabled

    def set_band_gain(self, frequency: int, gain: float) -> None:
        """
        Set gain for a specific band

        Args:
            frequency: Band frequency (31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)
            gain: Gain in dB (-12 to +12)
        """
        if frequency not in self._bands:
            logger.warning(f"Invalid frequency band: {frequency}")
            return

        # Clamp gain to valid range
        gain = max(self.MIN_GAIN, min(self.MAX_GAIN, gain))
        self._bands[frequency] = gain

        # Mark as custom preset if modified
        self._current_preset = "custom"

        logger.debug(f"EQ band {frequency}Hz set to {gain:+.1f}dB")

    def get_band_gain(self, frequency: int) -> float:
        """Get gain for a specific band"""
        return self._bands.get(frequency, 0.0)

    def get_all_gains(self) -> Dict[int, float]:
        """Get all band gains"""
        return self._bands.copy()

    def reset(self) -> None:
        """Reset all bands to 0dB (flat)"""
        for freq in self._bands:
            self._bands[freq] = 0.0
        self._current_preset = "flat"
        logger.info("Equalizer reset to flat")

    def apply_preset(self, preset_name: str) -> bool:
        """
        Apply a preset

        Args:
            preset_name: Name of preset to apply

        Returns:
            True if applied successfully
        """
        preset_name = preset_name.lower()

        # Check built-in presets
        if preset_name in BUILTIN_PRESETS:
            preset = BUILTIN_PRESETS[preset_name]
        # Check custom presets
        elif preset_name in self._custom_presets:
            preset = self._custom_presets[preset_name]
        else:
            logger.warning(f"Preset not found: {preset_name}")
            return False

        # Apply preset bands
        for freq, gain in preset.bands.items():
            if freq in self._bands:
                self._bands[freq] = gain

        self._current_preset = preset_name
        logger.info(f"Applied EQ preset: {preset.name}")
        return True

    def get_current_preset(self) -> str:
        """Get name of current preset"""
        return self._current_preset

    def get_preset_names(self, include_custom: bool = True) -> List[str]:
        """Get list of available preset names"""
        names = list(BUILTIN_PRESETS.keys())
        if include_custom:
            names.extend(self._custom_presets.keys())
        return names

    def get_preset_info(self, preset_name: str) -> Optional[EqualizerPreset]:
        """Get preset information"""
        preset_name = preset_name.lower()
        if preset_name in BUILTIN_PRESETS:
            return BUILTIN_PRESETS[preset_name]
        return self._custom_presets.get(preset_name)

    def save_custom_preset(self, name: str, description: str = "") -> bool:
        """
        Save current settings as custom preset

        Args:
            name: Name for the preset
            description: Optional description

        Returns:
            True if saved successfully
        """
        if not name:
            logger.warning("Preset name cannot be empty")
            return False

        # Normalize name
        preset_key = name.lower().replace(" ", "_")

        # Don't overwrite built-in presets
        if preset_key in BUILTIN_PRESETS:
            logger.warning(f"Cannot overwrite built-in preset: {name}")
            return False

        # Create preset
        preset = EqualizerPreset(name=name, bands=self._bands.copy(), description=description, is_custom=True)

        self._custom_presets[preset_key] = preset
        self._current_preset = preset_key

        # Save to file
        self._save_custom_presets()

        logger.info(f"Saved custom preset: {name}")
        return True

    def delete_custom_preset(self, name: str) -> bool:
        """Delete a custom preset"""
        preset_key = name.lower().replace(" ", "_")

        if preset_key in BUILTIN_PRESETS:
            logger.warning(f"Cannot delete built-in preset: {name}")
            return False

        if preset_key not in self._custom_presets:
            logger.warning(f"Custom preset not found: {name}")
            return False

        del self._custom_presets[preset_key]
        self._save_custom_presets()

        logger.info(f"Deleted custom preset: {name}")
        return True

    def _load_custom_presets(self) -> None:
        """Load custom presets from file"""
        if not self._presets_file.exists():
            return

        try:
            with open(self._presets_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for key, preset_data in data.items():
                preset = EqualizerPreset.from_dict(preset_data)
                preset.is_custom = True
                self._custom_presets[key] = preset

            logger.info(f"Loaded {len(self._custom_presets)} custom EQ presets")

        except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to load custom presets: {e}")

    def _save_custom_presets(self) -> None:
        """Save custom presets to file"""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)

            data = {key: preset.to_dict() for key, preset in self._custom_presets.items()}

            with open(self._presets_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self._custom_presets)} custom presets")

        except (OSError, TypeError, ValueError) as e:
            logger.error(f"Failed to save custom presets: {e}")

    def get_band_labels(self) -> List[str]:
        """Get display labels for all bands"""
        return [BAND_LABELS[band] for band in EqualizerBand]

    def get_band_frequencies(self) -> List[int]:
        """Get all band frequencies in order"""
        return [band.value for band in EqualizerBand]
