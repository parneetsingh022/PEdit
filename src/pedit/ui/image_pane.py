
from PySide6.QtCore import Qt, QRect, QSize, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QSizePolicy, QTabWidget, QTabBar, QInputDialog, QPushButton
)

from pedit.core.theme import color_theme


class ImageCanvas(QWidget):
    """A drawable canvas that maintains a target aspect ratio.

    It scales to fit inside its available space while preserving the
    (width,height) aspect tuple. The actual drawn canvas is centered.
    """

    DEFAULT_ASPECTS = [
        (1, 1),     # Square
        (3, 2),     # 3:2 photo
        (4, 3),     # Classic
        (5, 4),
        (16, 9),    # Widescreen landscape
        (9, 16),    # Portrait
    ]

    def __init__(self, aspect_ratio=(1, 1), background="#ffffff", parent=None):
        super().__init__(parent)
        self._aspect = aspect_ratio
        self._bg = background
        # Allow the widget to expand; we'll center the internal canvas area.
        sp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sp.setHeightForWidth(True)  # Tell layout system we keep ratio
        self.setSizePolicy(sp)
        # Enable stylesheet / custom painting background separation
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumSize(50, 50)

    # ---------------- Aspect Ratio API -----------------
    def aspectRatio(self):
        return self._aspect

    def setAspectRatio(self, w: int, h: int):
        if w <= 0 or h <= 0:
            return
        self._aspect = (w, h)
        self.updateGeometry()  # trigger relayout for new ratio
        self.update()

    def cycleAspectRatio(self):
        """Cycle through predefined aspect ratios."""
        try:
            idx = self.DEFAULT_ASPECTS.index(self._aspect)
            self._aspect = self.DEFAULT_ASPECTS[(idx + 1) % len(self.DEFAULT_ASPECTS)]
        except ValueError:
            self._aspect = self.DEFAULT_ASPECTS[0]
        self.update()

    # ---------------- Geometry Helpers -----------------
    def _compute_canvas_rect(self):
        avail = self.contentsRect()
        aw, ah = avail.width(), avail.height()
        rw, rh = self._aspect
        if rw == 0 or rh == 0 or aw <= 0 or ah <= 0:
            return avail
        scale = min(aw / rw, ah / rh)
        cw = int(rw * scale)
        ch = int(rh * scale)
        x = avail.x() + (aw - cw) // 2
        y = avail.y() + (ah - ch) // 2
        return QRect(x, y, cw, ch)

    def paintEvent(self, event):  # noqa: D401
        from PySide6.QtGui import QPainter, QColor, QPen
        painter = QPainter(self)
        try:
            # Fill background (pane behind canvas) with transparent or theme color
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

            canvas_rect = self._compute_canvas_rect()
            painter.fillRect(canvas_rect, QColor(self._bg))
            pen = QPen(QColor(color_theme.COLOR_BORDER))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(canvas_rect.adjusted(0, 0, -1, -1))
        finally:
            painter.end()

    # Optionally provide a size hint (scaled baseline)
    def sizeHint(self):
        rw, rh = self._aspect
        base_w = 480  # desired nominal width
        # compute height from aspect
        return QSize(base_w, int(base_w * rh / rw))

    def minimumSizeHint(self):
        return QSize(50, 50)

    # ---- Height-for-width support so layout preserves aspect automatically ----
    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w: int):
        rw, rh = self._aspect
        if rw == 0:
            return w
        return int(w * rh / rw)

    # Optional: ensure we never overflow vertically by capping width if needed
    def resizeEvent(self, event):
        # If the computed height would exceed available (due to outer constraints), we just repaint;
        # layout will already have picked a size that fits, thanks to heightForWidth.
        super().resizeEvent(event)


class ImagePane(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Tab system
        self.tabs = _ImageCanvasTabWidget(self)
        layout.addWidget(self.tabs, stretch=1)

        # Initial tab
        self.addNewCanvasTab("Untitled 1")

        self.setStyleSheet(
            f"background-color: {color_theme.COLOR_BACKGROUND_ALT};"
            "color:black;"
            f"border-right: 1px solid {color_theme.COLOR_BORDER};"
        )
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # ---- Canvas / Aspect convenience wrappers ------------------------------
    def currentCanvas(self) -> ImageCanvas | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, ImageCanvas) else None

    def setCanvasAspectRatio(self, w: int, h: int):
        canvas = self.currentCanvas()
        if canvas:
            canvas.setAspectRatio(w, h)

    def cycleAspectRatio(self):
        canvas = self.currentCanvas()
        if canvas:
            canvas.cycleAspectRatio()

    # ---- Tab management -----------------------------------------------------
    def addNewCanvasTab(self, label: str | None = None, aspect=(1,1)):
        canvas = ImageCanvas(aspect_ratio=aspect)
        idx = self.tabs.insertCanvasTab(canvas, label or self._nextDefaultLabel())
        self.tabs.setCurrentIndex(idx)
        return canvas

    def _nextDefaultLabel(self):
        base = "Untitled"
        existing = [self.tabs.tabText(i) for i in range(self.tabs.realTabCount())]
        n=1
        while f"{base} {n}" in existing:
            n+=1
        return f"{base} {n}"

    def renameCurrentTab(self, new_name: str):
        i = self.tabs.currentIndex()
        if 0 <= i < self.tabs.realTabCount():
            self.tabs.setTabText(i, new_name)


# ---------------------- Custom Tab Bar (no plus tab) -------------------------
class _ImageCanvasTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._onCloseRequested)

    def mouseDoubleClickEvent(self, event):
        idx = self.tabAt(event.pos())
        if idx != -1:
            old = self.tabText(idx)
            new_text, ok = QInputDialog.getText(self, "Rename Tab", "Tab name:", text=old)
            if ok and new_text.strip():
                self.setTabText(idx, new_text.strip())
        else:
            super().mouseDoubleClickEvent(event)

    def _onCloseRequested(self, index: int):
        self.removeTab(index)
        # If all tabs closed, signal up so widget can create a new one
        if self.count() == 0:
            parent = self.parent()
            if hasattr(parent, "_ensureOneTab"):
                parent._ensureOneTab()


class _ImageCanvasTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        bar = _ImageCanvasTabBar()
        self.setTabBar(bar)
        self.setDocumentMode(True)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._onClose)
        self.currentChanged.connect(self._onCurrentChanged)
        # Ensure plus tab stays last even after drag reordering
        bar.tabMoved.connect(self._onTabMoved)
        self._adjusting_tab_order = False

        # Add real plus page as last tab (so counts match pages)
        self._plus_page = QWidget()
        super().addTab(self._plus_page, "+")
        self._stripPlusClose()

        # Styling (no explicit close-button image so default icon shows)
        self.setStyleSheet(
            """
            QTabWidget::pane { border: 0; }
            QTabBar::tab {
                background: #2d2d2d;
                color: #d0d0d0;
                padding: 5px 14px;
                border: 1px solid #3f3f3f;
                border-bottom: 2px solid #1e1e1e;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #3a3a3a;
                color: #ffffff;
                border-bottom: 2px solid #4aa3ff;
            }
            QTabBar::tab:!selected:hover { background: #353535; }
            /* Plus tab appearance */
            QTabBar::tab:last {
                min-width: 34px;
                max-width: 34px;
                text-align: center;
                font-weight: 600;
                color: #5ec6ff;
            }
            QTabBar::tab:last:selected { border-bottom: 2px solid #5ec6ff; }
            """
        )

    # ---------- Plus tab helpers ---------------------------------
    def plusIndex(self):
        return self.indexOf(self._plus_page)

    def _stripPlusClose(self):
        pi = self.plusIndex()
        if pi != -1:
            for side in (QTabBar.LeftSide, QTabBar.RightSide):
                self.tabBar().setTabButton(pi, side, None)

    # Compatibility with previous API (exclude plus page)
    def realTabCount(self):
        return self.count() - 1

    def insertCanvasTab(self, canvas: ImageCanvas, label: str):
        pi = self.plusIndex()
        if pi == -1:
            # recreate plus page if somehow missing
            self._plus_page = QWidget()
            pi = super().addTab(self._plus_page, "+")
        idx = self.insertTab(pi, canvas, label)
        self.setCurrentIndex(idx)
        self._stripPlusClose()
        return idx

    def _onCurrentChanged(self, index: int):
        if index == self.plusIndex():
            parent = self.parent()
            # Guard: during construction ImagePane hasn't yet assigned self.tabs
            if isinstance(parent, ImagePane) and hasattr(parent, "tabs") and parent.tabs is self:
                parent.addNewCanvasTab()

    def _onTabMoved(self, from_index: int, to_index: int):
        # After any tab move, force plus tab to remain at last position.
        if self._adjusting_tab_order:
            return
        pi = self.plusIndex()
        if pi == -1:
            return
        last = self.count() - 1
        if pi != last:
            # Move plus tab back to end
            self._adjusting_tab_order = True
            self.tabBar().moveTab(pi, last)
            self._adjusting_tab_order = False
            # If user intended to select what they dragged, keep selection on that (unless it was plus)
            if from_index != pi:
                # Adjust potential index shift: if from_index was before original plus position and plus moved after, indices stable.
                # Just ensure we don't auto-select plus.
                if self.currentIndex() == self.plusIndex():
                    # Pick nearest non-plus tab
                    target = max(0, self.plusIndex()-1)
                    self.setCurrentIndex(target)

    def _onClose(self, index: int):
        if index == self.plusIndex():
            return
        self.removeTab(index)
        # If only plus page remains, auto add a new canvas tab
        if self.realTabCount() == 0:
            parent = self.parent()
            if isinstance(parent, ImagePane):
                parent.addNewCanvasTab()
        self._stripPlusClose()

    def _ensureOneTab(self):  # kept for compatibility with tab bar call
        if self.realTabCount() == 0:
            parent = self.parent()
            if isinstance(parent, ImagePane):
                parent.addNewCanvasTab()

