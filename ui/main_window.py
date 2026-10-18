import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,QInputDialog, QComboBox, QFileDialog,QMessageBox, QApplication)
from PyQt6.QtCore import QTimer, Qt, QEvent
from PyQt6.QtGui import QPainter, QPixmap, QCursor
from ui.column import Column
from core.data_manager import DataManager

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Management")
        self.resize(900, 600)

        self.bg_pixmap = None
        self._active_drag = None

        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.data_dir = os.path.join(app_dir, 'data')
        self.data_manager = DataManager(self.data_dir)
        main_layout = QVBoxLayout(self)
        top_bar = QHBoxLayout()

        self.board_combo = QComboBox()
        self.board_combo.setEditable(False)
        self.board_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 10px; font-size: 12px;
                border: 1px solid #555; border-radius: 3px;
                background-color: rgba(42, 42, 42, 0.8);
                color: white; min-width: 150px; font-family: Georgia, serif;
                combobox-popup: 0;
            }
            QComboBox:hover {
                background-color: rgba(58, 58, 58, 0.9); border-color: #777;
            }
            QComboBox::drop-down {
                border: none;
                background-color: rgba(42, 42, 42, 0.8);
                width: 30px;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a; border: 1px solid #555;
                border-radius: 3px; selection-background-color: #444;
                color: white; padding: 5px;
                font-family: Georgia, serif; font-size: 12px;
                outline: none;
            }
            QComboBox QAbstractItemView::item { padding: 5px 10px; color: white; }
            QComboBox QAbstractItemView::item:selected {
                background-color: #444; color: white;
            }
        """)

        button_style = """
            QPushButton {
                background-color: rgba(42, 42, 42, 0.8);
                border: 1px solid #555; border-radius: 4px;
                font-size: 16px; color: white;
            }
            QPushButton:hover { background-color: rgba(58, 58, 58, 0.9); }
        """

        self.new_board_btn = QPushButton("+")
        self.new_board_btn.setFixedSize(32, 32)
        self.new_board_btn.setToolTip("Create new space")
        self.new_board_btn.setStyleSheet(button_style)
        self.new_board_btn.clicked.connect(self.create_new_board)

        self.delete_board_btn = QPushButton("🗑")
        self.delete_board_btn.setFixedSize(32, 32)
        self.delete_board_btn.setToolTip("Delete space")
        self.delete_board_btn.setStyleSheet(button_style)
        self.delete_board_btn.clicked.connect(self.delete_current_board)

        self.bg_btn = QPushButton("🖼")
        self.bg_btn.setFixedSize(32, 32)
        self.bg_btn.setToolTip("Choose background")
        self.bg_btn.setStyleSheet(button_style)
        self.bg_btn.clicked.connect(self.choose_background)

        top_bar.addWidget(self.board_combo)
        top_bar.addWidget(self.new_board_btn)
        top_bar.addWidget(self.delete_board_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.bg_btn)

        main_layout.addLayout(top_bar)

        self.board_layout = QHBoxLayout()
        main_layout.addLayout(self.board_layout)

        self.boards = self.data_manager.get_boards()
        self.board_combo.addItems(self.boards)
        self.board_combo.currentTextChanged.connect(self.load_board)

        if self.boards:
            self.load_board(self.boards[0])

        QApplication.instance().installEventFilter(self)

    def _find_column_at(self, pos):
        w = QApplication.widgetAt(pos)
        while w is not None:
            if hasattr(w, 'cards_layout') and hasattr(w, 'scroll_area'):
                return w
            w = w.parent()
        return None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and self._active_drag is not None:
            col = self._find_column_at(QCursor.pos())
            if col is not None:
                bar = col.scroll_area.verticalScrollBar()
                bar.setValue(bar.value() - event.angleDelta().y() // 8)
                return True
        return super().eventFilter(obj, event)

    def choose_background(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose background", "",
            "Pic (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if file_path:
            self.bg_pixmap = QPixmap(file_path)
            current = self.board_combo.currentText()
            if current:
                self.data_manager.save_background(current, file_path)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            scaled = self.bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.fillRect(self.rect(), Qt.GlobalColor.black)
        painter.end()

    def create_new_board(self):
        name, ok = QInputDialog.getText(
            self, "New space", "Enter a name (for example, Home):"
        )
        if ok and name.strip():
            name = name.strip()
            if name not in self.boards:
                self.boards.append(name)
                self.board_combo.addItem(name)
                self.board_combo.setCurrentText(name)

    def delete_current_board(self):
        current = self.board_combo.currentText()
        if not current:
            return

        reply = QMessageBox.question(
            self, "Delete space",
            f"Delete space '{current}'?\nAll tasks will be permanently deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.delete_board(current)
            if current in self.boards:
                self.boards.remove(current)
            self.board_combo.removeItem(self.board_combo.currentIndex())

            if self.boards:
                self.load_board(self.boards[0])

    def load_board(self, board_name):
        if not board_name:
            return

        bg_path = self.data_manager.load_background(board_name)
        if bg_path and os.path.exists(bg_path):
            self.bg_pixmap = QPixmap(bg_path)
        else:
            self.bg_pixmap = None
        self.update()

        for i in reversed(range(self.board_layout.count())):
            item = self.board_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        data = self.data_manager.load(board_name)

        for title, cards in data.items():
            col = Column(title, show_add_button=(title == "New"))
            col.blockSignals(True)
            for card_data in cards:
                col.add_card(card_data["text"], card_data["color"],
                             card_data.get("date"))
            col.blockSignals(False)
            col.state_changed.connect(lambda bn=board_name: QTimer.singleShot(150,lambda: self.save_data(bn)))
            self.board_layout.addWidget(col)
        self.board_layout.addStretch()

    def save_data(self, board_name):
        new_data = {}
        for i in range(self.board_layout.count()):
            item = self.board_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), Column):
                col = item.widget()
                cards = []
                for j in range(col.cards_layout.count()):
                    card_item = col.cards_layout.itemAt(j)
                    if card_item.widget():
                        cards.append({
                            "text": card_item.widget().text,
                            "color": card_item.widget().color,
                            "date": card_item.widget().date
                        })
                new_data[col.title] = cards
        self.data_manager.save(board_name, new_data)