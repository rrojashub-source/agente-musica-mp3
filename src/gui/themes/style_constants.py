"""
Centralized style constants for NEXUS Music Manager GUI.

Eliminates duplicated inline setStyleSheet() calls by providing
named constants for common style patterns.

Usage::

    from gui.themes.style_constants import Styles

    self.title_label.setStyleSheet(Styles.HEADER_TITLE)
    self.status_label.setStyleSheet(Styles.TEXT_MUTED)
"""

from __future__ import annotations


class Colors:
    """Named color palette."""

    # Dark theme base
    BG_DARK = "#1e1e1e"
    BG_MEDIUM = "#2d2d2d"
    BG_LIGHT = "#3d3d3d"

    # Neon accent
    NEON_CYAN = "#00c8ff"
    NEON_CYAN_DARK = "#00a0cc"
    NEON_MAGENTA = "#a040a0"

    # Status
    GREEN = "#4CAF50"
    RED = "#f44336"
    ORANGE = "#ff9800"
    BLUE = "#2196F3"
    PURPLE = "#9b59b6"

    # Semantic status (Bootstrap-like)
    SUCCESS = "#27ae60"
    DANGER = "#e74c3c"
    WARNING = "#e67e22"
    INFO = "#3498db"

    # Text
    TEXT_PRIMARY = "#cccccc"
    TEXT_MUTED = "#888"
    TEXT_DIMMED = "#666"
    TEXT_FAINT = "#999"
    WHITE = "white"


class Styles:
    """Reusable stylesheet constants."""

    # ── Typography ──────────────────────────────────────────────

    HEADER_TITLE = "font-size: 18px; font-weight: bold;"
    HEADER_TITLE_PADDED = "font-size: 18px; font-weight: bold; padding: 10px;"
    SECTION_TITLE = "font-size: 16px; font-weight: bold;"
    SUBSECTION_TITLE = "font-size: 14pt; font-weight: bold;"
    LABEL_BOLD = "font-weight: bold; font-size: 12px;"
    LABEL_BOLD_PT = "font-weight: bold; font-size: 12pt;"
    LABEL_SMALL = "font-size: 12px;"
    LABEL_SMALL_MUTED = "font-size: 12px; color: #888;"
    LABEL_TINY = "font-size: 10px;"
    LABEL_TINY_MUTED = "font-size: 10px; color: #666;"
    LABEL_TINY_FADED = f"font-size: 10px; color: {Colors.TEXT_MUTED};"
    LABEL_TINY_FAINT = "font-size: 9px; color: #666;"
    LABEL_LARGE_PADDED = "font-size: 14px; padding: 10px;"

    # ── Text colors ─────────────────────────────────────────────

    TEXT_MUTED = f"color: {Colors.TEXT_MUTED};"
    TEXT_DIMMED = f"color: {Colors.TEXT_DIMMED};"
    TEXT_FAINT = f"color: {Colors.TEXT_FAINT};"
    TEXT_INFO_SMALL = f"color: {Colors.TEXT_MUTED}; font-size: 11px;"
    TEXT_INFO_PADDED = "margin-bottom: 10px; color: #666;"
    TEXT_INSTRUCTIONS = "padding: 5px; color: gray;"

    # ── Buttons ─────────────────────────────────────────────────

    BTN_PRIMARY = f"background: {Colors.INFO}; color: white; font-weight: bold;"
    BTN_SUCCESS = f"background: {Colors.SUCCESS}; color: white; padding: 8px 16px;"
    BTN_DANGER = f"background: {Colors.DANGER}; color: white;"
    BTN_WARNING = f"background: {Colors.WARNING}; color: white; padding: 8px 16px;"
    BTN_PURPLE = f"background: {Colors.PURPLE}; color: white; padding: 8px 16px;"
    BTN_INFO_PADDED = f"background: {Colors.INFO}; color: white; padding: 8px 16px;"
    BTN_TRANSPARENT = "background: transparent; border: none;"

    # ── Progress bar status ─────────────────────────────────────

    PROGRESS_COMPLETED = f"""
        QProgressBar {{
            border: 1px solid {Colors.GREEN};
            border-radius: 3px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {Colors.GREEN};
        }}
    """

    PROGRESS_FAILED = f"""
        QProgressBar {{
            border: 1px solid {Colors.RED};
            border-radius: 3px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {Colors.RED};
        }}
    """

    PROGRESS_PAUSED = f"""
        QProgressBar {{
            border: 1px solid {Colors.ORANGE};
            border-radius: 3px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {Colors.ORANGE};
        }}
    """

    PROGRESS_DOWNLOADING = f"""
        QProgressBar {{
            border: 1px solid {Colors.BLUE};
            border-radius: 3px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {Colors.BLUE};
        }}
    """

    PROGRESS_PENDING = """
        QProgressBar {
            border: 1px solid #9e9e9e;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #9e9e9e;
        }
    """

    # ── Equalizer ───────────────────────────────────────────────

    EQ_LABEL_NEUTRAL = "font-size: 10px; color: #666;"
    EQ_LABEL_BOOST = f"font-size: 10px; color: {Colors.GREEN};"
    EQ_LABEL_CUT = f"font-size: 10px; color: {Colors.RED};"

    # ── Status labels (bold + color) ─────────────────────────────

    STATUS_BOLD = "font-weight: bold;"
    STATUS_BOLD_GREEN = f"font-weight: bold; color: {Colors.GREEN};"
    STATUS_BOLD_RED = f"font-weight: bold; color: {Colors.RED};"
    STATUS_BOLD_ORANGE = f"font-weight: bold; color: {Colors.ORANGE};"
    STATUS_BOLD_DIMMED = f"font-weight: bold; color: {Colors.TEXT_DIMMED};"

    # ── Action buttons (padded with border-radius) ────────────

    BTN_ACTION = "QPushButton { padding: 8px 16px; font-size: 10pt;" " border-radius: 4px; }"

    # ── Fonts ──────────────────────────────────────────────────

    FONT_MONOSPACE = "font-family: monospace;"
    FONT_MONOSPACE_SMALL = "font-family: monospace; font-size: 11px;"

    # ── Status colors (plain, no bold) ─────────────────────────

    STATUS_GREEN = "color: green;"
    STATUS_RED = "color: red;"
    STATUS_GRAY_PADDED = "color: gray; padding: 20px;"

    # ── Section headers (with margin) ────────────────────────

    SECTION_HEADER_BOLD = "font-weight: bold; font-size: 13px; margin: 10px 0;"

    # ── Label sizes ──────────────────────────────────────────

    LABEL_10PT = "QLabel { font-size: 10pt; padding: 2px; }"
    LABEL_9PT = "font-size: 9pt;"
    LABEL_16PT_BOLD = "QLabel { font-size: 16pt; font-weight: bold; padding: 5px; }"

    # ── Card / stat value ────────────────────────────────────

    TEXT_DARK = "color: #333;"

    # ── URL / monospace box ──────────────────────────────────

    URL_LABEL = (
        "background: #2d2d2d; color: #ffffff; padding: 8px;"
        " border-radius: 4px; font-family: monospace; font-size: 10px;"
    )

    # ── Log text area ────────────────────────────────────────

    LOG_TEXT = (
        "font-family: monospace; font-size: 10px;" f" background: {Colors.BG_DARK}; color: {Colors.TEXT_PRIMARY};"
    )

    # ── Margin helpers ───────────────────────────────────────

    MARGIN_BOTTOM_10 = "margin-bottom: 10px;"

    # ── Misc ────────────────────────────────────────────────────

    BG_BLACK = "background-color: #000;"
    QR_FRAME = "background: white; border: 2px solid #666; border-radius: 6px;"
    FALLBACK_LABEL = "color: #888; font-size: 14px;"
