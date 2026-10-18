from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QLineEdit,QPushButton, QHBoxLayout, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.card import Card

class Column(QFrame):
    state_changed = pyqtSignal()

    def __init__(self, title, show_add_button=False):
        super().__init__()
        self.setAcceptDrops(True)
        self.title = title

        self.setFixedWidth(250)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        title_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            font-weight: bold;
            font-size: 12px;
            color: white;
            background: transparent;
            border: none;
            font-family: Georgia, serif;
        """)
        title_layout.addWidget(self.title_label)

        if show_add_button:
            self.add_btn = QPushButton("+")
            self.add_btn.setFixedSize(24, 24)
            self.add_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    font-size: 16px;
                    font-weight: bold;
                    font-family: Georgia, serif;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.15);
                    border-radius: 3px;
                }
            """)
            self.add_btn.clicked.connect(self.show_input_field)
            title_layout.addWidget(self.add_btn)

        title_layout.addStretch()
        main_layout.addLayout(title_layout)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter the card name...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                color: black;
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #555;
                border-radius: 3px;
                padding: 6px;
                font-family: Georgia, serif;
                font-size: 12px;
            }
        """)
        self.input_field.setAcceptDrops(False)
        self.input_field.returnPressed.connect(self.add_new_card)
        self.input_field.hide()
        main_layout.addWidget(self.input_field)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        scroll_widget = QFrame()
        self.cards_layout = QVBoxLayout(scroll_widget)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(5)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(self.scroll_area)

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 26, 26, 0.2);
                border-radius: 4px;
                border: none;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
        """)

    def show_input_field(self):
        self.input_field.show()
        self.input_field.clear()
        self.input_field.setFocus()

    def insert_card(self, index, text, color="white", date=None):
        card = Card(text, color, date)
        card.deleted.connect(self.on_card_deleted)
        card.color_changed.connect(self.state_changed.emit)
        card.text_changed.connect(self.state_changed.emit)
        index = max(0, min(index, self.cards_layout.count() - 1))
        self.cards_layout.insertWidget(index, card)
        self.state_changed.emit()
        return card

    def add_card(self, text, color="white", date=None):
        self.insert_card(self.cards_layout.count() - 1, text, color, date)

    def add_new_card(self):
        text = self.input_field.text().strip()
        if text:
            self.add_card(text)
            self.input_field.clear()
            self.input_field.hide()
            self.state_changed.emit()

    def on_card_deleted(self, card):
        self.cards_layout.removeWidget(card)
        self.state_changed.emit()

    def get_index_at_global(self, global_pos):
        local = self.scroll_area.widget().mapFromGlobal(global_pos)
        return self.get_index_at(local)

    def get_index_at(self, pos):
        for i in range(self.cards_layout.count() - 1):
            item = self.cards_layout.itemAt(i)
            if item.widget():
                widget = item.widget()
                if pos.y() < widget.y() + widget.height() / 2:
                    return i
        return self.cards_layout.count() - 1

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        raw_data = event.mimeData().text()
        parts = raw_data.split("|||")
        text = parts[0]
        color = parts[1] if len(parts) > 1 else "white"
        date = parts[2] if len(parts) > 2 else None
        local = self.scroll_area.widget().mapFromGlobal(
            event.globalPosition().toPoint()
        )
        index = self.get_index_at(local)
        self.insert_card(index, text, color, date)
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()