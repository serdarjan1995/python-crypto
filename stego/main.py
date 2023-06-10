import sys
import traceback
from PIL import Image
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (
    QGridLayout, QVBoxLayout, QHBoxLayout, QApplication, QWidget, QPushButton, QTextEdit, QLabel, QMessageBox,
    QFileDialog,
)
from stego.utils import reveal_message, hide_message
import logging
logging.basicConfig(level=logging.INFO)


class Stego(QWidget):
    WINDOW_W = 1000
    WINDOW_H = 700

    plain_text = ''
    filename = ''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(self.WINDOW_W, self.WINDOW_H)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self._construct_stego_widget())
        self.setLayout(main_layout)

    def _construct_stego_widget(self):
        self.stego_widget = QWidget(self)
        main_layout = QGridLayout()

        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)

        self.plain_text_text_edit = QTextEdit()
        self.plain_text_text_edit.textChanged.connect(
            lambda: setattr(self, 'plain_text', self.plain_text_text_edit.toPlainText()))
        main_layout.addWidget(self.plain_text_text_edit)

        right_panel_layout = QVBoxLayout()
        buttons_layout = QHBoxLayout()
        browse_file_button = QPushButton("Browse File")
        hide_message_button = QPushButton("Hide Message")
        reveal_message_button = QPushButton("Reveal Message")
        buttons_layout.addWidget(browse_file_button)
        buttons_layout.addWidget(hide_message_button)
        buttons_layout.addWidget(reveal_message_button)

        browse_file_button.clicked.connect(self.browse_files_button_clicked)
        hide_message_button.clicked.connect(self.hide_message_button_clicked)
        reveal_message_button.clicked.connect(self.reveal_message_button_clicked)

        right_panel_layout.addLayout(buttons_layout)
        self.image_pixmap = QLabel()
        right_panel_layout.addWidget(self.image_pixmap)
        main_layout.addLayout(right_panel_layout, 0, 1)

        self.stego_widget.setLayout(main_layout)
        return self.stego_widget

    def browse_files_button_clicked(self):
        filename = QFileDialog.getOpenFileName(self, 'Open image file', './', "Image files (*.jpg *.jpeg *.png *.bmp)")
        self.filename = filename[0]
        if self.filename:
            pixmap = QtGui.QPixmap(self.filename)
            pixmap = pixmap.scaled(self.WINDOW_W // 2, 300, QtCore.Qt.KeepAspectRatio)
            self.image_pixmap.setPixmap(pixmap)
            self.plain_text = ''
            self.plain_text_text_edit.setText(self.plain_text)

    def reveal_message_button_clicked(self):
        with Image.open(self.filename) as im:
            try:
                self.plain_text = reveal_message(im)
                self.plain_text_text_edit.setText(self.plain_text)
            except Exception as err:
                self.show_message_box("Error", repr(err))
                print(traceback.format_exc())

    def hide_message_button_clicked(self):
        with Image.open(self.filename) as im:
            try:
                self.plain_text = hide_message(im, self.plain_text)
                self.show_message_box("Success", "File saved ./STEGO_IMG.png")
            except Exception as err:
                self.show_message_box("Error", repr(err))
                print(traceback.format_exc())

    def show_message_box(self, title: str, msg: str, msg_info: str = None, msg_detail: str = None):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(msg)
        msg_box.setInformativeText(msg_info)
        msg_box.setDetailedText(msg_detail)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Stego()
    window.setWindowTitle('Stego')
    window.setWindowIcon(QtGui.QIcon('icon.png'))
    window.setFixedSize(window.WINDOW_W, window.WINDOW_H)
    window.show()
    sys.exit(app.exec_())
