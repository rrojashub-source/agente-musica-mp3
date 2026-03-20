"""
Tests for Audio Equalizer Module

Tests cover:
- Band gain adjustment
- Preset application
- Custom preset save/load
- Gain limits validation
"""

import pytest
import tempfile
import shutil

from core.audio_equalizer import AudioEqualizer, EqualizerPreset, EqualizerBand, BUILTIN_PRESETS, BAND_LABELS


class TestEqualizerBands:
    """Test equalizer band operations"""

    def test_default_bands_are_flat(self):
        """All bands should start at 0dB"""
        eq = AudioEqualizer()
        gains = eq.get_all_gains()

        for freq, gain in gains.items():
            assert gain == 0.0, f"Band {freq}Hz should be 0dB, got {gain}"

    def test_set_band_gain(self):
        """Setting band gain should work"""
        eq = AudioEqualizer()

        eq.set_band_gain(1000, 6.5)
        assert eq.get_band_gain(1000) == 6.5

        eq.set_band_gain(62, -3.0)
        assert eq.get_band_gain(62) == -3.0

    def test_gain_clamping_max(self):
        """Gain should be clamped to +12dB"""
        eq = AudioEqualizer()

        eq.set_band_gain(1000, 20.0)  # Over max
        assert eq.get_band_gain(1000) == 12.0

    def test_gain_clamping_min(self):
        """Gain should be clamped to -12dB"""
        eq = AudioEqualizer()

        eq.set_band_gain(1000, -20.0)  # Under min
        assert eq.get_band_gain(1000) == -12.0

    def test_invalid_frequency_ignored(self):
        """Invalid frequency should be ignored"""
        eq = AudioEqualizer()

        eq.set_band_gain(999, 5.0)  # Invalid frequency
        assert eq.get_band_gain(999) == 0.0

    def test_all_band_frequencies(self):
        """All expected frequencies should exist"""
        eq = AudioEqualizer()
        frequencies = eq.get_band_frequencies()

        expected = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
        assert frequencies == expected

    def test_band_labels(self):
        """Band labels should be readable"""
        eq = AudioEqualizer()
        labels = eq.get_band_labels()

        assert len(labels) == 10
        assert "31" in labels
        assert "1K" in labels
        assert "16K" in labels


class TestPresets:
    """Test preset functionality"""

    def test_builtin_presets_exist(self):
        """Built-in presets should exist"""
        assert "flat" in BUILTIN_PRESETS
        assert "rock" in BUILTIN_PRESETS
        assert "pop" in BUILTIN_PRESETS
        assert "jazz" in BUILTIN_PRESETS
        assert "classical" in BUILTIN_PRESETS

    def test_apply_flat_preset(self):
        """Applying flat preset should reset all bands"""
        eq = AudioEqualizer()

        # Modify some bands
        eq.set_band_gain(1000, 5.0)
        eq.set_band_gain(125, -3.0)

        # Apply flat
        eq.apply_preset("flat")

        gains = eq.get_all_gains()
        for gain in gains.values():
            assert gain == 0.0

    def test_apply_rock_preset(self):
        """Rock preset should have enhanced bass/treble"""
        eq = AudioEqualizer()
        eq.apply_preset("rock")

        # Rock typically has boosted bass and treble
        assert eq.get_band_gain(31) > 0  # Bass boost
        assert eq.get_band_gain(16000) > 0  # Treble boost

    def test_apply_invalid_preset(self):
        """Applying invalid preset should return False"""
        eq = AudioEqualizer()
        result = eq.apply_preset("nonexistent")
        assert result is False

    def test_get_current_preset(self):
        """Current preset should be tracked"""
        eq = AudioEqualizer()

        assert eq.get_current_preset() == "flat"

        eq.apply_preset("rock")
        assert eq.get_current_preset() == "rock"

    def test_manual_change_marks_custom(self):
        """Manual band change should mark preset as custom"""
        eq = AudioEqualizer()
        eq.apply_preset("rock")

        eq.set_band_gain(1000, 10.0)  # Manual change
        assert eq.get_current_preset() == "custom"

    def test_preset_info(self):
        """Preset info should include name and description"""
        eq = AudioEqualizer()

        preset = eq.get_preset_info("rock")
        assert preset is not None
        assert preset.name == "Rock"
        assert len(preset.description) > 0


class TestCustomPresets:
    """Test custom preset save/load"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_save_custom_preset(self, temp_config_dir):
        """Saving custom preset should work"""
        eq = AudioEqualizer(config_dir=temp_config_dir)

        # Set some bands
        eq.set_band_gain(1000, 5.0)
        eq.set_band_gain(4000, 3.0)

        # Save
        result = eq.save_custom_preset("My Test", "Test description")
        assert result is True

        # Check it exists
        assert "my_test" in eq.get_preset_names()

    def test_load_custom_preset(self, temp_config_dir):
        """Loading saved preset should restore bands"""
        eq = AudioEqualizer(config_dir=temp_config_dir)

        # Set and save
        eq.set_band_gain(1000, 7.5)
        eq.set_band_gain(250, -4.0)
        eq.save_custom_preset("Test Preset")

        # Reset and reload
        eq.reset()
        eq.apply_preset("test_preset")

        assert eq.get_band_gain(1000) == 7.5
        assert eq.get_band_gain(250) == -4.0

    def test_delete_custom_preset(self, temp_config_dir):
        """Deleting custom preset should work"""
        eq = AudioEqualizer(config_dir=temp_config_dir)

        eq.save_custom_preset("To Delete")
        assert "to_delete" in eq.get_preset_names()

        result = eq.delete_custom_preset("to_delete")
        assert result is True
        assert "to_delete" not in eq.get_preset_names()

    def test_cannot_delete_builtin(self, temp_config_dir):
        """Deleting built-in preset should fail"""
        eq = AudioEqualizer(config_dir=temp_config_dir)

        result = eq.delete_custom_preset("rock")
        assert result is False

    def test_cannot_overwrite_builtin(self, temp_config_dir):
        """Saving with built-in name should fail"""
        eq = AudioEqualizer(config_dir=temp_config_dir)

        result = eq.save_custom_preset("rock")  # Built-in name
        assert result is False

    def test_persistence_across_instances(self, temp_config_dir):
        """Custom presets should persist across instances"""
        # First instance - save preset
        eq1 = AudioEqualizer(config_dir=temp_config_dir)
        eq1.set_band_gain(500, 6.0)
        eq1.save_custom_preset("Persistent")

        # Second instance - should load it
        eq2 = AudioEqualizer(config_dir=temp_config_dir)
        assert "persistent" in eq2.get_preset_names()

        eq2.apply_preset("persistent")
        assert eq2.get_band_gain(500) == 6.0


class TestEqualizerState:
    """Test equalizer enable/disable state"""

    def test_enabled_by_default(self):
        """Equalizer should be enabled by default"""
        eq = AudioEqualizer()
        assert eq.is_enabled() is True

    def test_disable_enable(self):
        """Enabling/disabling should work"""
        eq = AudioEqualizer()

        eq.set_enabled(False)
        assert eq.is_enabled() is False

        eq.set_enabled(True)
        assert eq.is_enabled() is True

    def test_reset_to_flat(self):
        """Reset should return to flat"""
        eq = AudioEqualizer()

        eq.apply_preset("rock")
        eq.reset()

        assert eq.get_current_preset() == "flat"
        gains = eq.get_all_gains()
        for gain in gains.values():
            assert gain == 0.0


class TestEqualizerPresetDataclass:
    """Test EqualizerPreset dataclass"""

    def test_to_dict(self):
        """Preset should serialize to dict"""
        preset = EqualizerPreset(name="Test", bands={1000: 5.0, 2000: 3.0}, description="Test preset")

        d = preset.to_dict()
        assert d["name"] == "Test"
        assert "1000" in d["bands"]
        assert d["bands"]["1000"] == 5.0

    def test_from_dict(self):
        """Preset should deserialize from dict"""
        d = {"name": "Test", "bands": {"1000": 5.0, "2000": 3.0}, "description": "Test preset"}

        preset = EqualizerPreset.from_dict(d)
        assert preset.name == "Test"
        assert preset.bands[1000] == 5.0
        assert preset.bands[2000] == 3.0


class TestBandLabels:
    """Test band label constants"""

    def test_all_bands_have_labels(self):
        """All bands should have labels"""
        for band in EqualizerBand:
            assert band in BAND_LABELS

    def test_labels_are_readable(self):
        """Labels should be human-readable"""
        assert BAND_LABELS[EqualizerBand.BAND_1KHZ] == "1K"
        assert BAND_LABELS[EqualizerBand.BAND_16KHZ] == "16K"
        assert BAND_LABELS[EqualizerBand.BAND_31HZ] == "31"
