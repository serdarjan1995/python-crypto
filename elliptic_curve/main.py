import base64
import pickle
import sys
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QGridLayout, QVBoxLayout, QHBoxLayout,
    QApplication, QWidget, QPushButton, QTextEdit, QLabel, QTabWidget, QLineEdit, QCheckBox, QMessageBox,
)
from utils import Coor, EllipticCurve

p = 26959946667150639794667015087019630673557916260026308143510066298881
a = -3
b = 18958286285566608000408668544493926415504680968679321075787234672564

Gx = 19277929113566293071110308034699488026831934219452440156649784352033
Gy = 19926808758034470970197974370888749184205991990603949537637343198772
G = Coor(Gx, Gy)

P224 = EllipticCurve(a, b, p, G)


class EllipticCurveWidget(QWidget):
    WINDOW_W = 1000
    WINDOW_H = 700

    plain_text = ''
    cipher_text = ''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(self.WINDOW_W, self.WINDOW_H)

        main_layout = QVBoxLayout()

        # tabs
        self.tabs = QTabWidget()
        cipher_tab = self._construct_cipher_tab()

        self.tabs.addTab(cipher_tab, "Cipher")

        self.sender_private_key = None
        self.sender_public_key = None
        self.recipient_public_key = None
        self.shared_key = None
        self.keys_generated = False

        self.new_shared_key_on_encryption = False

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def _construct_cipher_tab(self):
        self.cipher_tab = QWidget(self)
        main_layout = QVBoxLayout()
        layout = QGridLayout()
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        self.cipher_tab.setLayout(main_layout)
        self.plain_text_text_edit = QTextEdit()
        self.plain_text_text_edit.textChanged.connect(
            lambda: setattr(self, 'plain_text', self.plain_text_text_edit.toPlainText()))
        self.cipher_text_text_edit = QTextEdit()
        self.cipher_text_text_edit.textChanged.connect(
            lambda: setattr(self, 'cipher_text', self.cipher_text_text_edit.toPlainText()))

        keys_layout = QVBoxLayout()
        private_key_layout = QHBoxLayout()
        private_key_layout.addWidget(QLabel('Private key: '))
        self.sender_private_key_line_edit = QLineEdit()
        private_key_layout.addWidget(self.sender_private_key_line_edit)

        generate_private_key_button = QPushButton("Generate Keys")
        generate_private_key_button.clicked.connect(self.generate_private_key_clicked)
        private_key_layout.addWidget(generate_private_key_button)

        keys_layout.addLayout(private_key_layout)

        public_key_layout = QHBoxLayout()
        public_key_layout.addWidget(QLabel('Public key: '))
        self.sender_public_key_line_edit = QLineEdit()
        public_key_layout.addWidget(self.sender_public_key_line_edit)
        keys_layout.addLayout(public_key_layout)

        shared_common_point_layout = QHBoxLayout()
        shared_common_point_layout.addWidget(QLabel('Shared key'))
        self.sender_shared_key_line_edit = QLineEdit()
        shared_common_point_layout.addWidget(self.sender_shared_key_line_edit)
        keys_layout.addLayout(shared_common_point_layout)

        recipient_public_key_layout = QHBoxLayout()
        recipient_public_key_layout.addWidget(QLabel('Recipient Public key'))
        self.recipient_public_key_line_edit = QLineEdit()
        recipient_public_key_layout.addWidget(self.recipient_public_key_line_edit)
        keys_layout.addLayout(recipient_public_key_layout)

        main_layout.addLayout(keys_layout)

        plain_text_label = QLabel("Plain text:")
        layout.addWidget(plain_text_label, 2, 0)
        layout.addWidget(self.plain_text_text_edit, 3, 0)

        self.cipher_key_layout = None
        self._construct_key_entry()

        cipher_text_label = QLabel("Cipher text:")
        layout.addWidget(cipher_text_label, 2, 1)
        layout.addWidget(self.cipher_text_text_edit, 3, 1)

        buttons_layout = QHBoxLayout()
        self.encrypt_button = QPushButton("Encrypt")
        self.encrypt_button.clicked.connect(self.encrypt_button_clicked)

        self.decrypt_button = QPushButton("Decrypt")
        self.decrypt_button.clicked.connect(self.decrypt_button_clicked)

        new_share_key_checkbox = QCheckBox("New Shared Key on Encryption")
        new_share_key_checkbox.toggled.connect(lambda: self.new_share_key_checkbox_clicked(new_share_key_checkbox))

        buttons_layout.addWidget(self.encrypt_button)
        buttons_layout.addWidget(self.decrypt_button)
        buttons_layout.addWidget(new_share_key_checkbox)
        main_layout.addLayout(buttons_layout)

        main_layout.addLayout(layout)
        return self.cipher_tab

    def generate_private_key_clicked(self):
        self.sender_private_key = P224.generate_random_n()
        self.sender_private_key_line_edit.setText(str(self.sender_private_key))
        self.sender_public_key = P224.scalar_multiplication(self.sender_private_key, G)
        self.sender_public_key_line_edit.setText(self.dump_bytes_pickle(self.sender_public_key))
        self.keys_generated = True

    def _construct_key_entry(self):
        self.cipher_key_layout = QVBoxLayout()
        buttons_horizontal_layout = QHBoxLayout()

        encrypt_button = QPushButton("Encrypt")
        decrypt_button = QPushButton("Decrypt")
        refresh_keys_button = QPushButton("Refresh keys")
        encrypt_button.clicked.connect(self.encrypt_button_clicked)
        decrypt_button.clicked.connect(self.decrypt_button_clicked)
        buttons_horizontal_layout.addWidget(encrypt_button)
        buttons_horizontal_layout.addWidget(decrypt_button)
        buttons_horizontal_layout.addWidget(refresh_keys_button)

        self.cipher_key_layout.addLayout(buttons_horizontal_layout)

    def dump_bytes_pickle(self, t):
        return self.to_base64(pickle.dumps(t))

    def load_bytes_pickle(self, t):
        return pickle.loads(self.from_base64(t))

    def to_base64(self, t):
        return base64.b64encode(t).decode()

    def from_base64(self, t):
        return base64.b64decode(t)

    def encrypt_button_clicked(self):
        if not self.keys_generated:
            self.show_message_box("Keys are empty", "Please generate keys")
            return
        plain_text = self.plain_text_text_edit.toPlainText()
        pubkey = self.recipient_public_key_line_edit.text()
        if not pubkey:
            self.show_message_box("Receiver pubkey is empty", "Please enter public key of the receiver")
            return
        self.recipient_public_key = pickle.loads(self.from_base64(pubkey))

        use_shared_key = self.shared_key
        if self.new_shared_key_on_encryption:
            use_shared_key = None

        encryption_point, encrypted_message = P224.encrypt(plain_text, self.recipient_public_key, use_shared_key)
        self.shared_key = encryption_point
        self.sender_shared_key_line_edit.setText(self.dump_bytes_pickle(encryption_point))
        self.cipher_text_text_edit.setText(encrypted_message)

    def decrypt_button_clicked(self):
        if not self.keys_generated:
            self.show_message_box("Keys are empty", "Please generate keys")
            return
        shared_key = self.sender_shared_key_line_edit.text()
        if not shared_key:
            self.show_message_box("Shared key is empty", "Please enter shared key")
            return
        try:
            cipher_text = self.cipher_text_text_edit.toPlainText()
            encryption_point = self.load_bytes_pickle(shared_key)
            decrypted_message = P224.decrypt(cipher_text, self.sender_private_key, encryption_point)
            self.plain_text_text_edit.setText(decrypted_message)
        except:
            self.plain_text_text_edit.setText("#ERR")

    def new_share_key_checkbox_clicked(self, new_share_key_checkbox):
        self.new_shared_key_on_encryption = new_share_key_checkbox.isChecked()

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
    window = EllipticCurveWidget()
    window.setWindowTitle('Elliptic curve cryptography')
    window.setWindowIcon(QtGui.QIcon('icon.png'))
    window.setFixedSize(window.WINDOW_W, window.WINDOW_H)
    window.show()
    sys.exit(app.exec_())
