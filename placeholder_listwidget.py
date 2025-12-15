import sys
import os
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QListWidget

#ポインタをウィジェットに出し入れすると
#drag leave received before drag enter
#という警告が出るが問題ない

class FolderDropListWidget(QListWidget):
    filesDropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_over = False
        self.setAcceptDrops(True)
        self.setDragEnabled(False)
        self.setDragDropMode(QListWidget.DropOnly)

    def _is_valid_drop(self, event):
        if not event.mimeData().hasUrls():
            return False

        for url in event.mimeData().urls():
            if not url.isLocalFile():
                return False
            if not os.path.isdir(url.toLocalFile()):
                return False

        return True

    def dragEnterEvent(self, event):
        self._drag_over = True
        self._drop_ok = self._is_valid_drop(event)

        if self._drop_ok:
            event.acceptProposedAction()
        else:
            event.accept()

        self.viewport().update()

    def dragMoveEvent(self, event):
        if self._drop_ok:
            event.acceptProposedAction()
        else:
            event.accept()

    def dragLeaveEvent(self, event):
        self._drag_over = False
        self.viewport().update()
        event.accept()

    def dropEvent(self, event):
        self._drag_over = False
        self.viewport().update()

        if not self._drop_ok:
            event.ignore()
            return

        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if os.path.isdir(url.toLocalFile())
        ]

        if paths:
            self.filesDropped.emit(paths)

        event.acceptProposedAction()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())

        if self._drag_over:
            if self._drop_ok:
                pen = QColor(0, 120, 215)      # 青
                brush = QColor(0, 120, 215, 40)
                text = "ドロップ"
            else:
                pen = QColor(200, 0, 0)        # 赤
                brush = QColor(200, 0, 0, 40)
                text = "フォルダではありません"

            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(self.viewport().rect().adjusted(2, 2, -2, -2))
            painter.drawText(self.viewport().rect(), Qt.AlignCenter, text)
            return


        if self.count() == 0:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(
                self.viewport().rect(),
                Qt.AlignCenter,
                "ここにフォルダを\nドラッグ＆ドロップ"
            )