
from PySide6.QtCore import Qt, QRect, QSize, Signal, QSignalBlocker  
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QSizePolicy, QTabWidget, QTabBar, QInputDialog, QPushButton, QToolButton
)
# Remove this line; use Signal from PySide6.QtCore instead.

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


# ---------------------- Custom Tab Bar (presentation-only) -------------------
class _ImageCanvasTabBar(QTabBar):
    """
    Presentation-only tab bar. It NEVER mutates tabs itself.
    All add/remove behavior is owned by _ImageCanvasTabWidget.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.setUsesScrollButtons(True)   # avoid squeezing close buttons off
        self.setExpanding(False)

    def mouseDoubleClickEvent(self, event):
        idx = self.tabAt(event.pos())
        if idx != -1:
            old = self.tabText(idx)
            new_text, ok = QInputDialog.getText(self, "Rename Tab", "Tab name:", text=old)
            if ok and new_text.strip():
                self.setTabText(idx, new_text.strip())
        else:
            super().mouseDoubleClickEvent(event)


class _ImageCanvasTabBar(QTabBar):
    """
    Presentation-only tab bar. It NEVER mutates tabs itself.
    Special behavior:
      - Treat the LAST tab labeled '+' as the add-tab trigger.
      - Clicking '+' emits plusClicked and DOES NOT change selection.
    """
    plusClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.setUsesScrollButtons(True)
        self.setExpanding(False)

    def isPlusIndex(self, index: int) -> bool:
        return 0 <= index < self.count() and self.tabText(index) == "+"

    def mousePressEvent(self, event):
        idx = self.tabAt(event.pos())
        if self.isPlusIndex(idx):
            # Consume the event and emit signal; do NOT let QTabBar change current tab.
            self.plusClicked.emit()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        idx = self.tabAt(event.pos())
        if idx != -1 and not self.isPlusIndex(idx):
            old = self.tabText(idx)
            new_text, ok = QInputDialog.getText(self, "Rename Tab", "Tab name:", text=old)
            if ok and new_text.strip():
                self.setTabText(idx, new_text.strip())
        else:
            # Ignore renaming for the '+' tab
            if not self.isPlusIndex(idx):
                super().mouseDoubleClickEvent(event)


# ---------------------- Custom Tab Widget ( '+' is the last tab ) -----------
class _ImageCanvasTabWidget(QTabWidget):
    """
    QTabWidget with a persistent '+' TAB pinned at the end (non-selecting trigger).
    - '+' is a real tab visually (so it sits right next to other tabs), but clicking it
      never changes selection; it emits plusClicked from the bar, and we add a canvas.
    - You can close the last real tab and end up with only the '+' tab; clicking '+'
      will add a new canvas immediately.
    - Parent is expected to implement ImagePane.addNewCanvasTab() which ultimately calls insertCanvasTab().
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Bar setup ---
        bar = _ImageCanvasTabBar()
        self.setTabBar(bar)
        self.setElideMode(Qt.ElideRight)  # elide long labels
        bar.plusClicked.connect(self._onPlusClicked)

        # '+' must stay at the end even after drag reordering
        self._adjusting_tab_order = False
        if hasattr(self.tabBar(), "tabMoved"):
            self.tabBar().tabMoved.connect(self._onTabMoved)

        # --- Widget-owned behaviors ---
        self.setDocumentMode(True)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._onClose)
        self.currentChanged.connect(self._onCurrentChanged)

        # --- Create persistent '+' page as last tab ---
        self._plus_page = QWidget()
        super().addTab(self._plus_page, "+")
        self._configurePlusTab()

        # --- Styling ---
        self.setStyleSheet(
            f"""
            QTabWidget::pane {{ border: 0; }}
            QTabBar::tab {{
                background: {color_theme.COLOR_SURFACE};
                color: {color_theme.COLOR_TEXT_SECONDARY};
                padding: 5px 18px;           /* room for close button */
                border: 1px solid {color_theme.COLOR_BORDER};
                border-bottom: 2px solid {color_theme.COLOR_BACKGROUND_DEEP};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-size: 12px;
                min-width: 88px;             /* keep close button usable when crowded */
            }}
            QTabBar::tab:selected {{
                background: {color_theme.COLOR_SURFACE_LIGHT};
                color: {color_theme.COLOR_TEXT_PRIMARY};
                border-bottom: 2px solid {color_theme.COLOR_PRIMARY};
            }}
            QTabBar::tab:!selected:hover {{ background: {color_theme.COLOR_SURFACE_LIGHT}; }}
            """
        )

    # ---------- Helpers -------------------------------------------------------
    def _plusIndex(self) -> int:
        return self.indexOf(self._plus_page) if hasattr(self, "_plus_page") else -1

    def _configurePlusTab(self) -> None:
        """Make '+' non-closable and pinned at the end."""
        pi = self._plusIndex()
        if pi == -1:
            return
        # Remove close buttons on '+' explicitly
        for side in (QTabBar.LeftSide, QTabBar.RightSide):
            self.tabBar().setTabButton(pi, side, None)
        self.setTabText(pi, "+")
        # Keep it last
        last = self.count() - 1
        if pi != last:
            self._adjusting_tab_order = True
            self.tabBar().moveTab(pi, last)
            self._adjusting_tab_order = False

    def _ensurePlusTab(self) -> None:
        """Ensure '+' page exists and is configured/pinned."""
        if not hasattr(self, "_plus_page") or self._plusIndex() == -1:
            self._plus_page = QWidget()
            super().addTab(self._plus_page, "+")
        self._configurePlusTab()

    def realTabCount(self) -> int:
        """Count only actual canvas widgets (ImageCanvas instances)."""
        c = 0
        for i in range(self.count()):
            w = self.widget(i)
            if w is not self._plus_page and isinstance(w, ImageCanvas):
                c += 1
        return c

    def insertCanvasTab(self, canvas: 'ImageCanvas', label: str) -> int:
        """
        Insert a new ImageCanvas tab right before the '+' tab and select it.
        Parent (ImagePane) should call this after creating the canvas.
        """
        self._ensurePlusTab()
        pi = self._plusIndex()
        idx = self.insertTab(pi, canvas, label) if pi != -1 else self.addTab(canvas, label)
        self.setCurrentIndex(idx)
        self._configurePlusTab()
        return idx

    # ---------- Events --------------------------------------------------------
    def _onPlusClicked(self) -> None:
        """Bar told us '+' was clicked; ask parent to create a new canvas."""
        parent = self.parent()
        if isinstance(parent, ImagePane) and hasattr(parent, "tabs") and parent.tabs is self:
            parent.addNewCanvasTab()
        # After parent adds, '+' will no longer be the last selected (we never selected it anyway).

    def _onCurrentChanged(self, index: int) -> None:
        """
        If Qt ever tries to select '+' (e.g., after closing the last canvas),
        we just ignore it and leave it selected; clicks on '+' still work because
        the bar emits plusClicked without changing selection.
        No auto-spawn here: user must click '+' to add a new tab.
        """
        # Nothing required; leaving '+' selected is okay since click still triggers via bar.

    def _onTabMoved(self, from_index: int, to_index: int) -> None:
        """Keep '+' pinned to the end after any move."""
        if self._adjusting_tab_order:
            return
        pi = self._plusIndex()
        if pi == -1:
            return
        last = self.count() - 1
        if pi != last:
            self._adjusting_tab_order = True
            self.tabBar().moveTab(pi, last)
            self._adjusting_tab_order = False

    def _onClose(self, index: int) -> None:
        """
        Close any tab (current or not). When the last real tab is closed,
        only '+' remains and is still clickable to add a new tab.
        """
        w = self.widget(index)
        if w is None or w is self._plus_page:
            return
        if not isinstance(w, ImageCanvas):
            return

        # Block signals during removal to avoid currentChanged races
        tb = self.tabBar()
        was_blocked_self = self.signalsBlocked()
        was_blocked_tb = tb.signalsBlocked() if tb is not None else False
        try:
            self.blockSignals(True)
            if tb is not None:
                tb.blockSignals(True)
            self.removeTab(index)
        finally:
            if tb is not None:
                tb.blockSignals(was_blocked_tb)
            self.blockSignals(was_blocked_self)

        # Optional: tidy up the widget
        try:
            w.deleteLater()
        except Exception:
            pass

        self._ensurePlusTab()

        # If some tabs remain, select a sensible neighbor; otherwise, leave only '+'
        if self.realTabCount() > 0:
            target = min(index, self.count() - 1)
            if self.widget(target) is self._plus_page and target - 1 >= 0:
                target -= 1
            self.setCurrentIndex(target)
        # else: zero real tabs -> only '+' present; clicking '+' adds a new one.