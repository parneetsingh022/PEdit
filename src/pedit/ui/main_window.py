import sys

from PySide6.QtCore import QSize, Qt, qVersion
from PySide6.QtWidgets import (
    QMainWindow, QMenu, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSizePolicy
)
from PySide6.QtGui import QAction 
import platform
import PySide6
from .side_pane import SidePane
from .image_pane import ImagePane

# Import package metadata (safe fallback if package not installed editable mode)
try:
    from pedit import __version__, __project__
except Exception:  # pragma: no cover - fallback
    __version__ = "unknown"
    __project__ = "imdge_editor"
from .menu_bar import MainMenu, MENU_SPEC, MENU_STYLESHEET

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        container = QWidget()

        self.setWindowTitle("PEdit")
        self.resize(1000,800)
        side_pane = SidePane()
        image_pane = ImagePane()
        # Layout: only the side pane + an expanding empty space (stretch).
        # SidePane already has QSizePolicy.Fixed (W) / Expanding (H) so it will
        # occupy full vertical height of the central area.
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        main_layout.addWidget(side_pane)
        # Give the image pane a stretch factor so it consumes all remaining width
        main_layout.addWidget(image_pane, 1)
        # Explicit stretch settings for clarity
        main_layout.setStretchFactor(side_pane, 0)
        main_layout.setStretchFactor(image_pane, 1)

        MainMenu.create_menu(self, MENU_SPEC, stylesheet=MENU_STYLESHEET)
        self.setCentralWidget(container)

    # ---- Menu action slots -------------------------------------------------
    def on_about(self):
        """Show an About dialog with version & environment info (like VS Code)."""
        # Collect extended metadata if available
        homepage = None
        try:  # Attempt to get Home-page from distribution metadata
            from importlib.metadata import metadata
            meta = metadata(__project__)
            homepage = meta.get("Home-page") or meta.get("Project-URL")
        except Exception:
            pass

        qt_version = None
        try:
            qt_version = qVersion()
        except Exception:
            qt_version = "unknown"

        info_rows = [
            ("Product", __project__),
            ("Version", __version__),
            ("PySide6", PySide6.__version__),
            ("Qt", qt_version),
            ("Python", platform.python_version()),
            ("Platform", platform.platform()),
        ]

        # Build HTML table for nice alignment
        rows_html = "".join(
            f"<tr><td style='padding:2px 8px;font-weight:600;' align='right'>{label}:</td>"
            f"<td style='padding:2px 4px;'>{value}</td></tr>" for label, value in info_rows
        )
        links_html = f"<p><a href='{homepage}' style='color:#6aa9ff;text-decoration:none;'>{homepage}</a></p>" if homepage else ""

        html = f"""
        <div style='font-family:Segoe UI,Arial,sans-serif;font-size:12px;'>
          <h3 style='margin:0 0 6px 0;'>{__project__}</h3>
          <table style='border-collapse:collapse;'>{rows_html}</table>
          {links_html}
          <p style='margin-top:4px;'>Press Ctrl+Q to exit the application.</p>
        </div>
        """

        # Use QMessageBox for simplicity (could be upgraded to custom QDialog later)
        box = QMessageBox(self)
        box.setWindowTitle(f"About {__project__}")
        box.setTextFormat(Qt.RichText)
        box.setText(html)
        box.setStandardButtons(QMessageBox.Ok)
        box.exec()
