"""
Tests for BaseTab — common base class for all tabs.

Validates:
- Init pattern (db_manager, _init_ui, _connect_signals)
- Progress infrastructure (show/hide/update, lazy properties)
- Worker integration (connect_worker)
- Common dialogs (show_error, show_confirm, etc.)
- Layout helpers (create_main_layout, create_header, create_group)

Phase 2.2 — Structural Refactoring
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QProgressBar, QLabel, QGroupBox
from PyQt6.QtCore import Qt, pyqtSignal, QThread
import sys

# Ensure QApplication exists
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

from gui.base.base_tab import BaseTab


class ConcreteTab(BaseTab):
    """Minimal concrete implementation for testing."""

    def _init_ui(self):
        layout = self.create_main_layout()
        self.add_progress_section(layout)


class ConcreteTabNoProgress(BaseTab):
    """Tab that doesn't explicitly add progress section (uses lazy properties)."""

    def _init_ui(self):
        self.create_main_layout()


class TestBaseTabInit(unittest.TestCase):
    """Test BaseTab initialization patterns."""

    def test_init_sets_db_manager(self):
        mock_db = Mock()
        tab = ConcreteTab(db_manager=mock_db)
        self.assertIs(tab.db, mock_db)
        tab.close()

    def test_init_without_db_manager(self):
        tab = ConcreteTab()
        self.assertIsNone(tab.db)
        tab.close()

    def test_init_calls_init_ui(self):
        tab = ConcreteTab()
        self.assertIsNotNone(tab.layout())
        tab.close()

    def test_abstract_init_ui_raises(self):
        with self.assertRaises(NotImplementedError):
            BaseTab()

    def test_connect_signals_called(self):
        """_connect_signals is called during init (no-op by default)."""
        tab = ConcreteTab()
        # No error means _connect_signals ran successfully
        self.assertIsNotNone(tab)
        tab.close()


class TestBaseTabProgress(unittest.TestCase):
    """Test progress bar and status label infrastructure."""

    def setUp(self):
        self.tab = ConcreteTab()

    def tearDown(self):
        self.tab.close()

    def test_add_progress_section_creates_widgets(self):
        self.assertIsInstance(self.tab.progress_bar, QProgressBar)
        self.assertIsInstance(self.tab.status_label, QLabel)

    def test_progress_bar_initially_hidden(self):
        self.assertFalse(self.tab.progress_bar.isVisible())

    def test_show_progress(self):
        self.tab.show_progress("Working...", 25)
        self.assertFalse(self.tab.progress_bar.isHidden())
        self.assertEqual(self.tab.progress_bar.value(), 25)
        self.assertEqual(self.tab.status_label.text(), "Working...")

    def test_update_progress(self):
        self.tab.show_progress()
        self.tab.update_progress(50, "Halfway")
        self.assertEqual(self.tab.progress_bar.value(), 50)
        self.assertEqual(self.tab.status_label.text(), "Halfway")

    def test_update_progress_without_message(self):
        self.tab.show_progress("Initial")
        self.tab.update_progress(75)
        self.assertEqual(self.tab.progress_bar.value(), 75)
        self.assertEqual(self.tab.status_label.text(), "Initial")  # Unchanged

    def test_hide_progress(self):
        self.tab.show_progress("Working...")
        self.tab.hide_progress("Done")
        self.assertFalse(self.tab.progress_bar.isVisible())
        self.assertEqual(self.tab.status_label.text(), "Done")

    def test_hide_progress_without_message(self):
        self.tab.show_progress("Working...")
        self.tab.hide_progress()
        self.assertFalse(self.tab.progress_bar.isVisible())


class TestBaseTabLazyProperties(unittest.TestCase):
    """Test lazy-created progress bar and status label."""

    def setUp(self):
        self.tab = ConcreteTabNoProgress()

    def tearDown(self):
        self.tab.close()

    def test_lazy_progress_bar(self):
        """Progress bar created on first access."""
        self.assertIsNone(self.tab._progress_bar)
        bar = self.tab.progress_bar
        self.assertIsInstance(bar, QProgressBar)
        self.assertIs(self.tab.progress_bar, bar)  # Same instance

    def test_lazy_status_label(self):
        """Status label created on first access."""
        self.assertIsNone(self.tab._status_label)
        label = self.tab.status_label
        self.assertIsInstance(label, QLabel)
        self.assertIs(self.tab.status_label, label)  # Same instance


class TestBaseTabLayoutHelpers(unittest.TestCase):
    """Test layout helper methods."""

    def test_create_main_layout(self):
        tab = ConcreteTab()
        layout = tab.layout()
        self.assertIsInstance(layout, QVBoxLayout)
        tab.close()

    def test_create_header(self):
        tab = ConcreteTab()
        header = tab.create_header("Test Title", "subtitle")
        self.assertIsNotNone(header)
        tab.close()

    def test_create_group_vertical(self):
        tab = ConcreteTab()
        group, layout = tab.create_group("Test Group")
        self.assertIsInstance(group, QGroupBox)
        self.assertIsInstance(layout, QVBoxLayout)
        tab.close()

    def test_create_group_horizontal(self):
        tab = ConcreteTab()
        group, layout = tab.create_group("Test Group", layout_type="horizontal")
        self.assertIsInstance(group, QGroupBox)
        tab.close()


class MockWorker(QThread):
    """Mock worker with standard signals."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def run(self):
        pass


class TestBaseTabWorkerIntegration(unittest.TestCase):
    """Test connect_worker method."""

    def setUp(self):
        self.tab = ConcreteTab()
        self.worker = MockWorker()

    def tearDown(self):
        self.tab.close()

    def test_connect_worker_shows_progress(self):
        self.tab.connect_worker(self.worker)
        self.assertFalse(self.tab.progress_bar.isHidden())
        self.assertEqual(self.tab.status_label.text(), "Starting...")

    def test_connect_worker_stores_active_worker(self):
        self.tab.connect_worker(self.worker)
        self.assertIs(self.tab._active_worker, self.worker)

    def test_connect_worker_disables_action_button(self):
        from PyQt6.QtWidgets import QPushButton
        btn = QPushButton("Test")
        btn.setEnabled(True)
        self.tab.connect_worker(self.worker, action_button=btn)
        self.assertFalse(btn.isEnabled())

    def test_connect_worker_default_progress_handler(self):
        self.tab.connect_worker(self.worker)
        self.worker.progress.emit(42, "Processing")
        self.assertEqual(self.tab.progress_bar.value(), 42)
        self.assertEqual(self.tab.status_label.text(), "Processing")

    def test_connect_worker_custom_progress_handler(self):
        custom_called = {}

        def custom_progress(pct, msg):
            custom_called['pct'] = pct
            custom_called['msg'] = msg

        self.tab.connect_worker(self.worker, on_progress=custom_progress)
        self.worker.progress.emit(55, "Custom")
        self.assertEqual(custom_called['pct'], 55)
        self.assertEqual(custom_called['msg'], "Custom")

    def test_connect_worker_finished_hides_progress(self):
        from PyQt6.QtWidgets import QPushButton
        btn = QPushButton("Test")
        results = {}

        def on_finished(result):
            results['value'] = result

        self.tab.connect_worker(
            self.worker,
            on_finished=on_finished,
            action_button=btn
        )
        self.worker.finished.emit("done")

        self.assertFalse(self.tab.progress_bar.isVisible())
        self.assertTrue(btn.isEnabled())
        self.assertEqual(results['value'], "done")
        self.assertIsNone(self.tab._active_worker)

    def test_connect_worker_error_shows_dialog(self):
        with patch.object(self.tab, 'show_error') as mock_error:
            self.tab.connect_worker(self.worker)
            self.worker.error.emit("Something failed")
            mock_error.assert_called_once_with("Something failed")
            self.assertIsNone(self.tab._active_worker)

    def test_connect_worker_custom_error_handler(self):
        errors = {}

        def on_error(msg):
            errors['msg'] = msg

        self.tab.connect_worker(self.worker, on_error=on_error)
        self.worker.error.emit("Custom error")
        self.assertEqual(errors['msg'], "Custom error")


class TestBaseTabDialogs(unittest.TestCase):
    """Test common dialog methods."""

    def setUp(self):
        self.tab = ConcreteTab()

    def tearDown(self):
        self.tab.close()

    def test_show_error(self):
        with patch('gui.base.base_tab.QMessageBox.critical') as mock:
            self.tab.show_error("Test error")
            mock.assert_called_once_with(self.tab, "Error", "Test error")

    def test_show_error_custom_title(self):
        with patch('gui.base.base_tab.QMessageBox.critical') as mock:
            self.tab.show_error("Test error", title="Custom")
            mock.assert_called_once_with(self.tab, "Custom", "Test error")

    def test_show_warning(self):
        with patch('gui.base.base_tab.QMessageBox.warning') as mock:
            self.tab.show_warning("Test warning")
            mock.assert_called_once_with(self.tab, "Warning", "Test warning")

    def test_show_success(self):
        with patch('gui.base.base_tab.QMessageBox.information') as mock:
            self.tab.show_success("Done!")
            mock.assert_called_once_with(self.tab, "Success", "Done!")

    def test_show_confirm_yes(self):
        from PyQt6.QtWidgets import QMessageBox
        with patch('gui.base.base_tab.QMessageBox.question',
                   return_value=QMessageBox.StandardButton.Yes):
            result = self.tab.show_confirm("Sure?")
            self.assertTrue(result)

    def test_show_confirm_no(self):
        from PyQt6.QtWidgets import QMessageBox
        with patch('gui.base.base_tab.QMessageBox.question',
                   return_value=QMessageBox.StandardButton.No):
            result = self.tab.show_confirm("Sure?")
            self.assertFalse(result)


class TestBaseTabInheritance(unittest.TestCase):
    """Test that refactored tabs correctly inherit from BaseTab."""

    def test_duplicates_tab_inherits_base_tab(self):
        from src.gui.tabs.duplicates_tab import DuplicatesTab
        self.assertTrue(issubclass(DuplicatesTab, BaseTab))

    def test_rename_tab_inherits_base_tab(self):
        from src.gui.tabs.rename_tab import RenameTab
        self.assertTrue(issubclass(RenameTab, BaseTab))

    def test_organize_tab_inherits_base_tab(self):
        from src.gui.tabs.organize_tab import OrganizeTab
        self.assertTrue(issubclass(OrganizeTab, BaseTab))

    def test_duplicates_tab_has_base_methods(self):
        from src.gui.tabs.duplicates_tab import DuplicatesTab
        mock_db = Mock()
        tab = DuplicatesTab(mock_db)
        self.assertTrue(hasattr(tab, 'show_error'))
        self.assertTrue(hasattr(tab, 'connect_worker'))
        self.assertTrue(hasattr(tab, 'show_progress'))
        tab.close()

    def test_rename_tab_connect_worker_pattern(self):
        from src.gui.tabs.rename_tab import RenameTab
        mock_db = Mock()
        tab = RenameTab(mock_db)
        self.assertTrue(hasattr(tab, 'connect_worker'))
        self.assertTrue(hasattr(tab, '_on_worker_error'))
        tab.close()

    def test_organize_tab_connect_worker_pattern(self):
        from src.gui.tabs.organize_tab import OrganizeTab
        mock_db = Mock()
        tab = OrganizeTab(mock_db)
        self.assertTrue(hasattr(tab, 'connect_worker'))
        self.assertTrue(hasattr(tab, '_on_worker_error'))
        tab.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
