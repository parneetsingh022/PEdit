
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QSizePolicy
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
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.canvas = ImageCanvas()
        # Center the canvas; it will internally manage aspect fitting
        layout.addWidget(self.canvas, stretch=1)

        self.setLayout(layout)

        self.setStyleSheet(
            f"background-color: {color_theme.COLOR_BACKGROUND_ALT};"
            "color:black;"
            f"border-right: 1px solid {color_theme.COLOR_BORDER};"
        )
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # Convenience API to change aspect ratio from outside
    def setCanvasAspectRatio(self, w: int, h: int):
        self.canvas.setAspectRatio(w, h)
    def cycleAspectRatio(self):
        self.canvas.cycleAspectRatio()

