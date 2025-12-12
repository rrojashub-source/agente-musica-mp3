"""
Tests for LRC Parser

Tests cover:
- Basic LRC parsing
- Timestamp parsing (multiple formats)
- Metadata extraction
- Current line lookup
- LRC generation
- File operations
"""
import pytest
import tempfile
import os
from pathlib import Path

from core.lrc_parser import LRCParser, LRCLine, LRCMetadata, parse_lrc, load_lrc


class TestLRCLine:
    """Test LRCLine dataclass"""

    def test_time_seconds(self):
        """Should convert ms to seconds"""
        line = LRCLine(time_ms=45500, text="Test")
        assert line.time_seconds == 45.5

    def test_time_formatted(self):
        """Should format time as [MM:SS.xx]"""
        line = LRCLine(time_ms=125300, text="Test")
        # 125.3 seconds = 2:05.30
        assert line.time_formatted == "[02:05.30]"

    def test_str_representation(self):
        """Should convert to LRC line format"""
        line = LRCLine(time_ms=12000, text="Hello world")
        assert str(line) == "[00:12.00]Hello world"

    def test_zero_time(self):
        """Should handle zero timestamp"""
        line = LRCLine(time_ms=0, text="Start")
        assert line.time_formatted == "[00:00.00]"
        assert str(line) == "[00:00.00]Start"


class TestLRCParser:
    """Test LRC parsing functionality"""

    def test_parse_simple_lrc(self):
        """Should parse simple LRC content"""
        lrc = """[00:12.00]Line one
[00:15.50]Line two
[00:18.00]Line three"""

        parser = LRCParser()
        lines, metadata = parser.parse(lrc)

        assert len(lines) == 3
        assert lines[0].time_ms == 12000
        assert lines[0].text == "Line one"
        assert lines[1].time_ms == 15500
        assert lines[2].time_ms == 18000

    def test_parse_centiseconds_2digit(self):
        """Should parse 2-digit centiseconds"""
        lrc = "[00:12.50]Test"
        lines, _ = LRCParser().parse(lrc)

        assert lines[0].time_ms == 12500

    def test_parse_centiseconds_3digit(self):
        """Should parse 3-digit milliseconds"""
        lrc = "[00:12.500]Test"
        lines, _ = LRCParser().parse(lrc)

        assert lines[0].time_ms == 12500

    def test_parse_metadata(self):
        """Should extract metadata tags"""
        lrc = """[ar:The Beatles]
[ti:Yesterday]
[al:Help!]
[00:12.00]Line"""

        parser = LRCParser()
        lines, metadata = parser.parse(lrc)

        assert metadata.artist == "The Beatles"
        assert metadata.title == "Yesterday"
        assert metadata.album == "Help!"
        assert len(lines) == 1

    def test_parse_offset(self):
        """Should apply timing offset"""
        lrc = """[offset:500]
[00:10.00]Line"""

        parser = LRCParser()
        lines, metadata = parser.parse(lrc)

        assert metadata.offset == 500
        assert lines[0].time_ms == 10500  # 10000 + 500

    def test_parse_multiple_timestamps(self):
        """Should handle multiple timestamps on same line"""
        lrc = "[00:12.00][00:24.00]Chorus"

        parser = LRCParser()
        lines, _ = parser.parse(lrc)

        assert len(lines) == 2
        assert lines[0].time_ms == 12000
        assert lines[0].text == "Chorus"
        assert lines[1].time_ms == 24000
        assert lines[1].text == "Chorus"

    def test_parse_empty_lines(self):
        """Should handle empty lines gracefully"""
        lrc = """[00:12.00]Line one

[00:15.00]Line two"""

        parser = LRCParser()
        lines, _ = parser.parse(lrc)

        assert len(lines) == 2

    def test_parse_empty_content(self):
        """Should handle empty content"""
        lines, metadata = LRCParser().parse("")

        assert len(lines) == 0
        assert metadata.artist is None

    def test_lines_sorted_by_time(self):
        """Should sort lines by timestamp"""
        lrc = """[00:20.00]Third
[00:10.00]First
[00:15.00]Second"""

        parser = LRCParser()
        lines, _ = parser.parse(lrc)

        assert lines[0].text == "First"
        assert lines[1].text == "Second"
        assert lines[2].text == "Third"


class TestCurrentLine:
    """Test current line lookup"""

    @pytest.fixture
    def sample_lines(self):
        """Create sample lyrics lines"""
        return [
            LRCLine(time_ms=0, text="Intro"),
            LRCLine(time_ms=5000, text="Verse 1"),
            LRCLine(time_ms=10000, text="Verse 2"),
            LRCLine(time_ms=15000, text="Chorus"),
            LRCLine(time_ms=25000, text="Outro"),
        ]

    def test_get_current_line_exact(self, sample_lines):
        """Should get exact line at timestamp"""
        parser = LRCParser()
        line = parser.get_current_line(sample_lines, 5000)

        assert line.text == "Verse 1"

    def test_get_current_line_between(self, sample_lines):
        """Should get previous line when between timestamps"""
        parser = LRCParser()
        line = parser.get_current_line(sample_lines, 7500)

        assert line.text == "Verse 1"

    def test_get_current_line_before_first(self, sample_lines):
        """Should return first line at time 0"""
        parser = LRCParser()
        line = parser.get_current_line(sample_lines, 0)

        assert line.text == "Intro"

    def test_get_current_line_after_last(self, sample_lines):
        """Should get last line after last timestamp"""
        parser = LRCParser()
        line = parser.get_current_line(sample_lines, 30000)

        assert line.text == "Outro"

    def test_get_current_line_empty(self):
        """Should return None for empty list"""
        parser = LRCParser()
        line = parser.get_current_line([], 5000)

        assert line is None

    def test_get_current_index(self, sample_lines):
        """Should return correct index"""
        parser = LRCParser()

        assert parser.get_current_index(sample_lines, 5000) == 1
        assert parser.get_current_index(sample_lines, 12000) == 2
        assert parser.get_current_index(sample_lines, 0) == 0

    def test_get_surrounding_lines(self, sample_lines):
        """Should get lines around current position"""
        parser = LRCParser()
        surrounding, current_idx = parser.get_surrounding_lines(
            sample_lines, 10000, before=1, after=2
        )

        # At 10000ms, current is "Verse 2" (index 2)
        # Should return lines 1-4 (Verse 1, Verse 2, Chorus, Outro)
        assert len(surrounding) == 4
        assert surrounding[1].text == "Verse 2"
        assert current_idx == 1  # Position in surrounding list


class TestLRCGeneration:
    """Test LRC generation"""

    def test_generate_with_timings(self):
        """Should generate LRC with provided timings"""
        parser = LRCParser()
        lyrics = """First line
Second line
Third line"""
        timings = [0, 5000, 10000]

        lrc = parser.generate_lrc(lyrics, timings)

        assert "[00:00.00]First line" in lrc
        assert "[00:05.00]Second line" in lrc
        assert "[00:10.00]Third line" in lrc

    def test_generate_with_metadata(self):
        """Should include metadata in generated LRC"""
        parser = LRCParser()
        lyrics = "Test line"
        timings = [0]
        metadata = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album'
        }

        lrc = parser.generate_lrc(lyrics, timings, metadata)

        assert "[ti:Test Song]" in lrc
        assert "[ar:Test Artist]" in lrc
        assert "[al:Test Album]" in lrc

    def test_generate_without_timings(self):
        """Should generate placeholder timings"""
        parser = LRCParser()
        lyrics = """Line 1
Line 2
Line 3"""

        lrc = parser.generate_lrc(lyrics)

        # Should have 5-second intervals
        assert "[00:00.00]Line 1" in lrc
        assert "[00:05.00]Line 2" in lrc
        assert "[00:10.00]Line 3" in lrc


class TestFileOperations:
    """Test LRC file operations"""

    @pytest.fixture
    def temp_lrc_file(self):
        """Create temporary LRC file"""
        content = """[ar:Test Artist]
[ti:Test Song]
[00:12.00]First line
[00:15.00]Second line"""

        fd, path = tempfile.mkstemp(suffix='.lrc')
        os.write(fd, content.encode('utf-8'))
        os.close(fd)

        yield path

        os.unlink(path)

    def test_parse_file(self, temp_lrc_file):
        """Should parse LRC file from disk"""
        parser = LRCParser()
        lines, metadata = parser.parse_file(temp_lrc_file)

        assert metadata.artist == "Test Artist"
        assert metadata.title == "Test Song"
        assert len(lines) == 2

    def test_parse_file_not_found(self):
        """Should handle missing file gracefully"""
        parser = LRCParser()
        lines, metadata = parser.parse_file("/nonexistent/file.lrc")

        assert len(lines) == 0
        assert metadata.artist is None

    def test_find_lrc_file(self):
        """Should find LRC file next to audio"""
        temp_dir = tempfile.mkdtemp()

        # Create audio and lrc files
        audio_path = os.path.join(temp_dir, "song.mp3")
        lrc_path = os.path.join(temp_dir, "song.lrc")

        Path(audio_path).touch()
        Path(lrc_path).write_text("[00:00.00]Test")

        parser = LRCParser()
        found = parser.find_lrc_file(audio_path)

        assert found == lrc_path

        # Cleanup
        os.unlink(audio_path)
        os.unlink(lrc_path)
        os.rmdir(temp_dir)

    def test_find_lrc_file_not_found(self):
        """Should return None when LRC not found"""
        parser = LRCParser()
        found = parser.find_lrc_file("/path/to/song.mp3")

        assert found is None


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_parse_lrc_function(self):
        """Should work as convenience function"""
        lrc = "[00:12.00]Test line"
        lines, metadata = parse_lrc(lrc)

        assert len(lines) == 1
        assert lines[0].text == "Test line"

    def test_load_lrc_function(self):
        """Should load and parse file"""
        # Create temp file
        fd, path = tempfile.mkstemp(suffix='.lrc')
        os.write(fd, b"[00:00.00]Test")
        os.close(fd)

        lines, metadata = load_lrc(path)

        assert len(lines) == 1

        os.unlink(path)
