from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QMenu, QSizePolicy,QPlainTextEdit, QTextEdit, QHBoxLayout, QLabel,QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QKeyEvent, QTextOption
from datetime import datetime

class CardTextEdit(QPlainTextEdit):
    editing_finished = pyqtSignal()
    editing_cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: rgba(255, 255, 255, 0.95);
                color: black;
                border: 1px solid #0079bf;
                border-radius: 3px;
                padding: 4px;
                font-family: Georgia, serif;
                font-size: 10px;
            }
        """)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.editing_finished.emit()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Return and not (
                event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.editing_finished.emit()
        elif event.key() == Qt.Key.Key_Escape:
            self.editing_cancelled.emit()
        else:
            super().keyPressEvent(event)

class CardDisplayText(QTextEdit):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setPlainText(text)
        self.setReadOnly(True)
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: black;
                padding: 0px;
                margin: 0px;
                font-family: Georgia, serif;
                font-size: 10px;
            }
        """)
        self.setFixedHeight(40)

    def setPlainText(self, text):
        super().setPlainText(text)

class Card(QFrame):
    deleted = pyqtSignal(object)
    color_changed = pyqtSignal()
    text_changed = pyqtSignal()
    COLLAPSED_HEIGHT = 70
    MAX_EXPANDED_HEIGHT = 200

    def __init__(self, text, color="white", date=None):
        super().__init__()
        self.text = text
        self.color = color
        self.date = date or datetime.now().strftime('%d-%m-%Y')
        self.is_expanded = False

        self.setFixedWidth(210)
        self.setFixedHeight(self.COLLAPSED_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self.display_widget = CardDisplayText(self.text)
        self.display_widget.setFixedWidth(190)
        layout.addWidget(self.display_widget)

        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 2, 0, 0)

        self.date_label = QLabel(self.date)
        self.date_label.setStyleSheet("""
            color: #666;
            font-family: Georgia, serif;
            font-size: 9px;
            background: transparent;
            border: none;
        """)
        bottom_layout.addWidget(self.date_label)
        bottom_layout.addStretch()

        self.expand_btn = QPushButton("▼")
        self.expand_btn.setFixedSize(24, 20)
        self.expand_btn.setToolTip("Expand / collapse")
        self.expand_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: #666;
                border: none;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.4);
                color: #333;
            }
        """)
        self.expand_btn.clicked.connect(self.toggle_expand)
        bottom_layout.addWidget(self.expand_btn)
        layout.addLayout(bottom_layout)
        self.edit_widget = CardTextEdit()
        self.edit_widget.setFixedWidth(190)
        self.edit_widget.setFixedHeight(90)
        self.edit_widget.hide()
        layout.addWidget(self.edit_widget)
        self.edit_widget.editing_finished.connect(self.finish_editing)
        self.edit_widget.editing_cancelled.connect(self.cancel_editing)
        self.update_style()
        self._drag_start_pos = None
        self._dragging = False
        self._preview = None

    def update_style(self):
        rgba_color = self._get_rgba_color(self.color, 0.5)
        self.setStyleSheet(f"""
            background-color: {rgba_color};
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 4px;
        """)

    def _get_rgba_color(self, color, alpha):
        color_map = {
            "white": (255, 255, 255),
            "#ffcccc": (255, 204, 204),
            "#ffffcc": (255, 255, 204),
            "#ccffcc": (204, 255, 204),
            "#cce5ff": (204, 229, 255)
        }
        if color in color_map:
            r, g, b = color_map[color]
            return f"rgba({r}, {g}, {b}, {alpha})"
        return color

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.display_widget.setPlainText(self.text)
            doc = self.display_widget.document()
            doc.setTextWidth(190)
            needed_height = int(doc.size().height()) + 4
            new_height = min(max(needed_height, 40), self.MAX_EXPANDED_HEIGHT)
            self.display_widget.setFixedHeight(new_height)

            total_height = new_height + 30
            self.setFixedHeight(total_height)
            self.expand_btn.setText("▲")
        else:
            self.display_widget.setPlainText(self.text)
            self.display_widget.setFixedHeight(40)
            self.setFixedHeight(self.COLLAPSED_HEIGHT)
            self.expand_btn.setText("▼")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint()
            self._dragging = False
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self._drag_start_pos is None:
            return
        if not self._dragging:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            if delta.manhattanLength() < 15:
                return
            self._dragging = True
            self._start_drag()
        if self._preview is not None:
            g = event.globalPosition().toPoint()
            self._preview.move(g.x() + 12, g.y() + 12)
        event.accept()

    def _start_drag(self):
        self._preview = QLabel()
        self._preview.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self._preview.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._preview.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._preview.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        pixmap = self.grab()
        self._preview.setPixmap(pixmap)
        self._preview.resize(pixmap.size())

        g = self.mapToGlobal(QPoint(0, 0))
        self._preview.move(g.x() + 12, g.y() + 12)
        self._preview.show()

        main_window = self._find_main_window()
        if main_window is not None:
            main_window._active_drag = self

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)
            return
        if self._dragging:
            self._finish_drag(event.globalPosition().toPoint())
        self._drag_start_pos = None
        self._dragging = False
        event.accept()

    def _finish_drag(self, global_pos):
        main_window = self._find_main_window()
        if main_window is None:
            self._cleanup_drag()
            return
        target_column = main_window._find_column_at(global_pos)
        source_column = self._find_parent_column()
        if target_column is None or source_column is None:
            self._cleanup_drag()
            return
        new_index = target_column.get_index_at_global(global_pos)
        if target_column is source_column:
            old_index = source_column.cards_layout.indexOf(self)
            if old_index == new_index:
                self._cleanup_drag()
                return

            source_column.cards_layout.removeWidget(self)
            if new_index > old_index:
                new_index -= 1
            new_index = max(0, min(new_index, source_column.cards_layout.count() - 1))
            source_column.cards_layout.insertWidget(new_index, self)
            source_column.state_changed.emit()
        else:
            try:
                self.deleted.disconnect()
                self.color_changed.disconnect()
                self.text_changed.disconnect()
            except:
                pass
            source_column.cards_layout.removeWidget(self)
            self.deleted.connect(target_column.on_card_deleted)
            self.color_changed.connect(target_column.state_changed.emit)
            self.text_changed.connect(target_column.state_changed.emit)
            new_index = max(0, min(new_index, target_column.cards_layout.count() - 1))
            target_column.cards_layout.insertWidget(new_index, self)
            self.show()
            source_column.state_changed.emit()
            target_column.state_changed.emit()
        self._cleanup_drag()

    def _cleanup_drag(self):
        if self._preview is not None:
            self._preview.close()
            self._preview.deleteLater()
            self._preview = None
        main_window = self._find_main_window()
        if main_window is not None:
            main_window._active_drag = None
        self._dragging = False

    def _find_parent_column(self):
        w = self.parent()
        while w is not None:
            if hasattr(w, 'cards_layout') and hasattr(w, 'scroll_area'):
                return w
            w = w.parent()
        return None

    def _find_main_window(self):
        w = self.parent()
        while w is not None:
            if hasattr(w, 'board_layout'):
                return w
            w = w.parent()
        return None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_editing()
        else:
            super().mouseDoubleClickEvent(event)

    def start_editing(self):
        self.display_widget.hide()
        self.date_label.hide()
        self.expand_btn.hide()
        self.edit_widget.show()
        self.edit_widget.setPlainText(self.text)
        self.edit_widget.setFocus()
        self.edit_widget.selectAll()

    def finish_editing(self):
        new_text = self.edit_widget.toPlainText().strip()
        if new_text and new_text != self.text:
            self.text = new_text
            self.is_expanded = False
            self.display_widget.setPlainText(self.text)
            self.display_widget.setFixedHeight(40)
            self.setFixedHeight(self.COLLAPSED_HEIGHT)
            self.expand_btn.setText("▼")
            self.text_changed.emit()
        self.edit_widget.hide()
        self.display_widget.show()
        self.date_label.show()
        self.expand_btn.show()

    def cancel_editing(self):
        self.edit_widget.hide()
        self.display_widget.show()
        self.date_label.show()
        self.expand_btn.show()

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        menu_style = """
            QMenu {
                background-color: #2a2a2a; color: white;
                border: 1px solid #555; border-radius: 4px;
                padding: 5px; font-family: Georgia, serif; font-size: 12px;
            }
            QMenu::item:selected { background-color: #444; }
        """
        context_menu.setStyleSheet(menu_style)

        color_menu = context_menu.addMenu("Color")
        color_menu.setStyleSheet(menu_style)

        colors = {
            "White": "white",
            "Red": "#ffcccc",
            "Yellow": "#ffffcc",
            "Green": "#ccffcc",
            "Blue": "#cce5ff"
        }

        for name, hex_code in colors.items():
            action = color_menu.addAction(name)
            action.triggered.connect(lambda checked, c=hex_code: self.set_color(c))
        context_menu.addSeparator()
        delete_action = context_menu.addAction("Delete")
        action = context_menu.exec(event.globalPos())

        if action == delete_action:
            self.deleted.emit(self)
            self.deleteLater()

    def set_color(self, color):
        self.color = color
        self.update_style()
        self.color_changed.emit()