
from PySide6.QtCore import Qt, QRect, QSize, Signal, QSignalBlocker  
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSizePolicy, QTabWidget, QTabBar, QInputDialog, QPushButton, QToolButton,
    QDialog, QLineEdit, QLabel, QScrollArea, QFrame
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


class _AspectPreview(QFrame):
    """Clickable preview card representing an aspect ratio visually."""
    clicked = Signal(object)  # emits self when selected
    def __init__(self, ratio: tuple[int, int], theme, parent=None):
        super().__init__(parent)
        self.ratio = ratio
        self.theme = theme
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(88, 74)
        self.setMaximumWidth(110)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Plain)
        self._selected = False
        self.setStyleSheet("")  # we'll paint manually
        self.setAttribute(Qt.WA_Hover, True)

    def setSelected(self, sel: bool):
        if self._selected != sel:
            self._selected = sel
            self.update()

    def isSelected(self):
        return self._selected

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Emit a signal instead of assuming parent has a method
            self.clicked.emit(self)
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):  # draws card + inner rectangle representing ratio
        from PySide6.QtGui import QPainter, QColor, QPen, QBrush
        painter = QPainter(self)
        r = self.rect().adjusted(4, 4, -4, -4)
        bg = QColor(self.theme.COLOR_SURFACE_LIGHT if self._selected else self.theme.COLOR_SURFACE)
        painter.fillRect(r, bg)
        # Border
        pen = QPen(QColor(self.theme.COLOR_PRIMARY if self._selected else self.theme.COLOR_BORDER))
        pen.setWidth(2 if self._selected else 1)
        painter.setPen(pen)
        painter.drawRoundedRect(r, 6, 6)

        # Compute inner preview area based on aspect
        aw, ah = self.ratio
        if aw <= 0 or ah <= 0:
            return
        avail_w = r.width() - 14
        avail_h = r.height() - 28
        scale = min(avail_w / aw, avail_h / ah)
        pw = int(aw * scale)
        ph = int(ah * scale)
        px = r.x() + (r.width() - pw)//2
        py = r.y() + 10 + (avail_h - ph)//2
        inner_rect = QRect(px, py, pw, ph)
        painter.setBrush(QBrush(QColor(self.theme.COLOR_BACKGROUND)))
        pen2 = QPen(QColor(self.theme.COLOR_PRIMARY if self._selected else self.theme.COLOR_TEXT_SECONDARY))
        pen2.setWidth(1)
        painter.setPen(pen2)
        painter.drawRect(inner_rect)

        # Label below preview
        painter.setPen(QColor(self.theme.COLOR_TEXT_PRIMARY if self._selected else self.theme.COLOR_TEXT_SECONDARY))
        label = f"{aw}:{ah}"
        painter.drawText(r.adjusted(0, ph + 12, 0, 0), Qt.AlignHCenter | Qt.AlignTop, label)
        painter.end()


class NewCanvasDialog(QDialog):
    """Custom styled dialog with visual aspect ratio templates."""
    def __init__(self, parent=None, default_name: str = "Untitled", aspects=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Canvas")
        self.setModal(True)
        self.setObjectName("NewCanvasDialog")
        self.theme = color_theme
        if aspects is None:
            aspects = ImageCanvas.DEFAULT_ASPECTS
        self._aspects = aspects
        self._selected_ratio = (1, 1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        title = QLabel("New Canvas")
        title.setObjectName("DialogTitle")
        font = title.font()
        font.setPointSize(font.pointSize() + 2)
        font.setBold(True)
        title.setFont(font)
        outer.addWidget(title)

        # Name row
        name_row = QHBoxLayout()
        name_label = QLabel("Name:")
        self.name_edit = QLineEdit()
        self.name_edit.setText(default_name)
        name_row.addWidget(name_label)
        name_row.addWidget(self.name_edit, 1)
        outer.addLayout(name_row)

        # Aspect ratio previews in a scroll area (in case many)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(10)
        grid.setContentsMargins(4, 4, 4, 4)
        self._cards: list[_AspectPreview] = []
        cols = 4
        for idx, ratio in enumerate(aspects):
            card = _AspectPreview(ratio, self.theme, parent=container)
            self._cards.append(card)
            row = idx // cols
            col = idx % cols
            grid.addWidget(card, row, col)
            card.clicked.connect(self.aspectCardClicked)
            if ratio == (1, 1):
                card.setSelected(True)
        scroll.setWidget(container)
        outer.addWidget(scroll, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.create_btn = QPushButton("Create")
        self.cancel_btn = QPushButton("Cancel")
        self.create_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.create_btn)
        outer.addLayout(btn_row)

        self._applyStyles()
        self.resize(520, 420)

    # Aspect card click handler (called from _AspectPreview)
    def aspectCardClicked(self, card: _AspectPreview):
        for c in self._cards:
            c.setSelected(c is card)
        self._selected_ratio = card.ratio

    def selectedName(self) -> str:
        return self.name_edit.text().strip() or "Untitled"

    def selectedAspect(self) -> tuple[int, int]:
        return self._selected_ratio

    def _applyStyles(self):
        self.setStyleSheet(
            f"""
            QDialog#NewCanvasDialog {{
                background: {self.theme.COLOR_SURFACE};
                color: {self.theme.COLOR_TEXT_PRIMARY};
                border: 1px solid {self.theme.COLOR_BORDER};
            }}
            QLabel#DialogTitle {{
                color: {self.theme.COLOR_TEXT_PRIMARY};
            }}
            QLineEdit {{
                background: {self.theme.COLOR_BACKGROUND};
                border: 1px solid {self.theme.COLOR_BORDER};
                padding: 4px 6px;
                border-radius: 4px;
                color: {self.theme.COLOR_TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 1px solid {self.theme.COLOR_PRIMARY};
            }}
            QPushButton {{
                background: {self.theme.COLOR_SURFACE_LIGHT};
                border: 1px solid {self.theme.COLOR_BORDER};
                padding: 6px 14px;
                border-radius: 5px;
                color: {self.theme.COLOR_TEXT_PRIMARY};
            }}
            QPushButton:hover {{ background: {self.theme.COLOR_BACKGROUND_ALT}; }}
            QPushButton:pressed {{ background: {self.theme.COLOR_BACKGROUND}; }}
        """
        )


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

    # ---- New Canvas Dialog --------------------------------------------------
    def promptNewCanvas(self):
        """Open dialog to gather name & aspect; returns (name, (w,h)) or None on cancel."""
        default_name = self._nextDefaultLabel()
        dlg = NewCanvasDialog(self, default_name=default_name, aspects=ImageCanvas.DEFAULT_ASPECTS)
        if dlg.exec() == QDialog.Accepted:
            return dlg.selectedName(), dlg.selectedAspect()
        return None

    def createCanvasViaDialog(self):
        res = self.promptNewCanvas()
        if res is None:
            return None
        name, aspect = res
        return self.addNewCanvasTab(name, aspect=aspect)


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
        """Bar told us '+' was clicked; show dialog for new canvas parameters."""
        parent = self.parent()
        if isinstance(parent, ImagePane) and hasattr(parent, "tabs") and parent.tabs is self:
            parent.createCanvasViaDialog()
        # After possible add, '+' remains last; selection stays on previous tab.

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