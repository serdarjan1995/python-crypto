import sys
import string
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (
    QGridLayout, QVBoxLayout, QHBoxLayout, QLayout,
    QApplication, QWidget, QPushButton, QTextEdit, QLabel, QTabWidget, QLineEdit,
    QRadioButton, QSpinBox, QCheckBox, QListWidget, QScrollArea, QGroupBox
)
from utils import (
    rot_n_generator, random_shuffle_str, chr_frequency, substitution_cipher, get_top_n_letter_words,
    get_substitution_map_from_freqs, cal_error_rate, substitute_word_as
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class BarChartCanvas(FigureCanvasQTAgg):

    def __init__(self, parent, x_values, y_values, x_label, y_label, title='', width=5, height=4, dpi=100):
        figure = Figure(figsize=(width, height), dpi=dpi)
        figure.subplots_adjust(left=0.12, bottom=0.2, right=0.95, top=0.90)
        self.axes = figure.add_subplot(111)
        # creating the bar plot
        self.axes.bar(x_values, y_values, color='green', width=0.4)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.get_ylabel()
        self.axes.set_title(title)
        super().__init__(figure)
        self.setParent(parent)
        self.updateGeometry()
        self.draw()

    def update_data(self, x_values, y_values, color='green'):
        x_label = self.axes.get_xlabel()
        y_label = self.axes.get_ylabel()
        title = self.axes.get_title()
        self.axes.clear()
        self.axes.bar(x_values, y_values, color=color, width=0.4)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.set_title(title)
        self.draw()
        self.flush_events()


class CipherTextAnalysis(QWidget):
    ROT_CIPHER = 'rot_cipher'
    SUBSTITUTION_CIPHER = 'substitution_cipher'
    ROT_KEY_SIZE_MAX = 32
    ROT_KEY_SIZE_MIN = 1
    WINDOW_W = 1000
    WINDOW_H = 700
    cipher_type = ROT_CIPHER
    rot_key_size = 5
    substitution_cipher_keys = ''
    substitution_cipher_values = ''
    WHITESPACES = 'whitespace'
    DIGITS = 'digits'
    PUNCTUATION = 'punctuation'
    skip_symbols = [WHITESPACES]
    plain_text = ''
    cipher_text = ''
    top_words_count = 3
    top_words_letters = 3
    is_sample_text_analyzed = False
    success_rate = 0
    error_rate = 0
    crack_keys = None
    substitution_words_line_edits = ([], [],)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(self.WINDOW_W, self.WINDOW_H)

        main_layout = QVBoxLayout()

        # tabs
        self.tabs = QTabWidget()
        cipher_tab = self._construct_cipher_tab()
        char_analysis_tab = self._construct_char_analysis_tab()
        sample_text_tab = self._construct_sample_text_tab()
        crack_tab = self._construct_crack_tab()

        self.tabs.addTab(cipher_tab, "Cipher")
        self.tabs.addTab(char_analysis_tab, "Char analysis")
        self.tabs.addTab(sample_text_tab, "Sample text")
        self.tabs.addTab(crack_tab, "Crack")
        self.tabs.currentChanged.connect(self.tabs_changed)

        # initial disabled crack_tab
        self.tabs.setTabEnabled(3, self.is_sample_text_analyzed)

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def tabs_changed(self, value):
        if value == 0:
            # Char analysis tab
            pass
        elif value == 1:
            # Char analysis tab
            self.refresh_char_analysis_tab()
        elif value == 2:
            # Crack tab
            pass

    def _construct_cipher_tab(self):
        self.cipher_tab = QWidget(self)
        layout = QGridLayout()
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        self.cipher_tab.setLayout(layout)
        self.plain_text_text_edit = QTextEdit()
        self.plain_text_text_edit.textChanged.connect(
            lambda: setattr(self, 'plain_text', self.plain_text_text_edit.toPlainText()))
        self.cipher_text_text_edit = QTextEdit()
        self.cipher_text_text_edit.textChanged.connect(
            lambda: setattr(self, 'cipher_text', self.cipher_text_text_edit.toPlainText()))

        radio_buttons = self._construct_cipher_tab_radio_selectors()
        layout.addLayout(radio_buttons, 0, 0)

        plain_text_label = QLabel("Plain text:")
        layout.addWidget(plain_text_label, 2, 0)
        layout.addWidget(self.plain_text_text_edit, 3, 0)

        self.cipher_key_layout = None
        self._construct_key_entry()

        cipher_text_label = QLabel("Cipher text:")
        layout.addWidget(cipher_text_label, 2, 1)
        layout.addWidget(self.cipher_text_text_edit, 3, 1)
        return self.cipher_tab

    def _construct_char_analysis_tab(self):
        self.char_analysis_tab = QWidget(self)
        layout = QGridLayout()
        self.char_analysis_tab.setLayout(layout)
        self.char_analysis_plain_text_text_edit = QTextEdit()
        self.char_analysis_cipher_text_text_edit = QTextEdit()

        layout.addWidget(QLabel("Plain text:"), 0, 0)
        layout.addWidget(self.char_analysis_plain_text_text_edit, 1, 0)

        # plain text chart
        self.plain_text_frequency_chart = BarChartCanvas(
            self,
            x_values=[],
            y_values=[],
            x_label='Letters',
            y_label='Frequency',
            title="Plain Text Character Frequency Table",
            height=3,
        )
        layout.addWidget(self.plain_text_frequency_chart, 1, 1)

        # cipher text chart
        self.cipher_text_frequency_chart = BarChartCanvas(
            self,
            x_values=[],
            y_values=[],
            x_label='Letters',
            y_label='Frequency',
            title="Cipher Text Character Frequency Table",
            height=3,
        )
        layout.addWidget(self.cipher_text_frequency_chart, 3, 1)

        layout.addWidget(QLabel("Cipher text:"), 2, 0)
        layout.addWidget(self.char_analysis_cipher_text_text_edit, 3, 0)
        return self.char_analysis_tab

    def _construct_sample_text_tab(self):
        self.sample_text_tab = QWidget(self)
        layout = QGridLayout()
        self.sample_text_tab.setLayout(layout)

        self.sample_text_text_edit = QTextEdit()

        layout.addWidget(QLabel("Sample text:"), 0, 0)
        layout.addWidget(self.sample_text_text_edit, 1, 0)

        analyze_sample_text_button = QPushButton("Analyze Sample Text")
        analyze_sample_text_button.clicked.connect(self.analyze_sample_text_button_clicked)
        layout.addWidget(analyze_sample_text_button, 0, 1)

        # plain text chart
        right_panel_layout = QGridLayout()
        right_panel_layout.setRowMinimumHeight(0, int(self.WINDOW_H / 3))
        right_panel_layout.setRowMinimumHeight(1, int(self.WINDOW_H / 3))
        self.sample_text_frequency_chart = BarChartCanvas(
            self,
            x_values=[],
            y_values=[],
            x_label='Letters',
            y_label='Frequency',
            title="Sample Text Character Frequency Table",
            height=3,
        )
        right_panel_layout.addWidget(self.sample_text_frequency_chart, 0, 0)
        self.top_words_in_sample_text_list_box = QListWidget()
        list_words_layout = self.construct_list_top_words_menu(self.top_words_in_sample_text_list_box,
                                                               self.sample_text_text_edit)
        right_panel_layout.addLayout(list_words_layout, 1, 0)
        layout.addLayout(right_panel_layout, 1, 1)
        right_panel_layout.setAlignment(QtCore.Qt.AlignTop)

        return self.sample_text_tab

    def construct_list_top_words_menu(self, top_words_list_box, textedit):
        vertical_layout = QVBoxLayout()

        list_menu_layout = QHBoxLayout()
        list_menu_layout.addWidget(QLabel('List'))

        top_words_count_input = QSpinBox()
        top_words_count_input.setSingleStep(1)
        top_words_count_input.setRange(1, 4)
        top_words_count_input.setValue(self.top_words_count)
        top_words_count_input.valueChanged.connect(lambda x: setattr(self, 'top_words_count', x))
        list_menu_layout.addWidget(top_words_count_input)

        list_menu_layout.addWidget(QLabel('top'))

        letter_size_input = QSpinBox()
        letter_size_input.setSingleStep(1)
        letter_size_input.setRange(1, 4)
        letter_size_input.setValue(self.top_words_letters)
        letter_size_input.valueChanged.connect(lambda x: setattr(self, 'top_words_letters', x))
        list_menu_layout.addWidget(letter_size_input)

        list_menu_layout.addWidget(QLabel('letter words'))

        list_button = QPushButton("List")
        list_button.clicked.connect(lambda: self.list_top_words_button_clicked(top_words_list_box, textedit))
        list_menu_layout.addWidget(list_button)
        vertical_layout.addLayout(list_menu_layout)
        vertical_layout.addWidget(top_words_list_box)

        return vertical_layout

    def _construct_crack_tab(self):
        self.crack_tab = QWidget(self)
        main_layout = QGridLayout()
        self.crack_tab.setLayout(main_layout)

        main_layout.addWidget(QLabel('Keys:'), 0, 0)
        refresh_crack_tab_button = QPushButton("Refresh and populate key mapping")
        refresh_crack_tab_button.clicked.connect(self.crack_tab_refresh_button_clicked)

        group_box = QGroupBox()
        group_box.setMaximumWidth(100)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(group_box)
        self.crack_tab_keys_layout = QGridLayout()
        group_box.setLayout(self.crack_tab_keys_layout)
        main_layout.addWidget(scroll_area, 1, 0)
        main_layout.setColumnStretch(0, 2)
        main_layout.setColumnStretch(1, 5)
        main_layout.setColumnStretch(2, 5)

        main_layout.addWidget(refresh_crack_tab_button, 0, 1)
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel('Decipher Text:'))
        crack_button = QPushButton("Crack")
        crack_button.clicked.connect(self.crack_button_clicked)
        h_layout.addWidget(crack_button)
        main_layout.addLayout(h_layout, 0, 2)

        self.decipher_text_text_edit = QTextEdit()
        main_layout.addWidget(self.decipher_text_text_edit, 1, 2)

        self.top_words_in_decipher_text_list_box = QListWidget()
        self.substitute_words_button = QPushButton('Substitute words')
        self.substitute_words_button.clicked.connect(self.substitute_words_button_clicked)
        self.substitute_words_button.setDisabled(not self.substitution_words_line_edits[0])

        self.substitute_words_layout = QGridLayout()
        vertical_layout = QVBoxLayout()
        top_words_list_layout = self.construct_list_top_words_menu(self.top_words_in_decipher_text_list_box,
                                                                   self.decipher_text_text_edit)
        vertical_layout.addLayout(top_words_list_layout)
        vertical_layout.addWidget(self.substitute_words_button)
        vertical_layout.addLayout(self.substitute_words_layout)

        main_layout.addLayout(vertical_layout, 1, 1)

        self.success_rate_label = QLabel(f'Success rate: {self.success_rate}')
        self.error_rate_label = QLabel(f'Error rate: {self.error_rate}')
        main_layout.addWidget(self.error_rate_label, 2, 1)
        main_layout.addWidget(self.success_rate_label, 2, 2)

        return self.crack_tab

    def crack_tab_refresh_button_clicked(self):
        self._remove_layout_and_widgets(self.crack_tab_keys_layout)
        self.crack_keys = None
        cipher_text_frequency = chr_frequency(self.cipher_text, skip_symbols=string.whitespace)
        sample_text_frequency = chr_frequency(self.sample_text_text_edit.toPlainText(), skip_symbols=string.whitespace)
        self.crack_keys = get_substitution_map_from_freqs(cipher_text_frequency, sample_text_frequency)
        for i, freq in enumerate(self.crack_keys.items()):
            key_line_edit = QLineEdit()
            key_line_edit.setMaximumWidth(30)
            key_line_edit.setMinimumHeight(20)
            key_line_edit.setText(f"{freq[0]}")
            value_line_edit = QLineEdit()
            value_line_edit.setMaximumWidth(30)
            value_line_edit.setMinimumHeight(20)
            value_line_edit.setText(f"{freq[1]}")
            self.crack_tab_keys_layout.addWidget(key_line_edit, i+1, 0)
            self.crack_tab_keys_layout.addWidget(value_line_edit, i+1, 1)

    def crack_button_clicked(self):
        if not self.crack_keys:
            return
        decipher_text = substitution_cipher(self.cipher_text.upper(), self.crack_keys)
        self.decipher_text_text_edit.setPlainText(decipher_text)
        self.error_rate = cal_error_rate(self.plain_text, decipher_text)
        self.success_rate = round(100.0 - self.error_rate, 2)
        self.refresh_success_rate_labels()

    def refresh_success_rate_labels(self):
        self.success_rate_label.setText(f'Success rate: {self.success_rate} %')
        self.error_rate_label.setText(f'Error rate: {self.error_rate} %')

    def refresh_char_analysis_tab(self):
        self.char_analysis_plain_text_text_edit.setPlainText(self.plain_text)
        self.char_analysis_cipher_text_text_edit.setPlainText(self.cipher_text)

        plain_text_char_frequency = chr_frequency(self.plain_text, skip_symbols=string.whitespace)
        self.plain_text_frequency_chart.update_data(
            plain_text_char_frequency.keys(), plain_text_char_frequency.values()
        )

        cipher_text_char_frequency = chr_frequency(self.cipher_text, skip_symbols=string.whitespace)
        self.cipher_text_frequency_chart.update_data(
            cipher_text_char_frequency.keys(), cipher_text_char_frequency.values()
        )

    def _construct_cipher_tab_radio_selectors(self):
        layout = QHBoxLayout()
        layout.setObjectName('cipher_tab_layout')
        rot_cipher_radio_select = QRadioButton("ROT Cipher")
        rot_cipher_radio_select.setChecked(self.cipher_type == self.ROT_CIPHER)
        rot_cipher_radio_select.cipher = self.ROT_CIPHER
        rot_cipher_radio_select.toggled.connect(self.cipher_radio_button_clicked)
        layout.addWidget(rot_cipher_radio_select, 0)

        substitution_cipher_radio_select = QRadioButton("Substitution Cipher")
        rot_cipher_radio_select.setChecked(self.cipher_type == self.SUBSTITUTION_CIPHER)
        substitution_cipher_radio_select.cipher = self.SUBSTITUTION_CIPHER
        substitution_cipher_radio_select.toggled.connect(self.cipher_radio_button_clicked)
        layout.addWidget(substitution_cipher_radio_select, 1)

        return layout

    def _construct_key_entry(self):
        self.cipher_key_layout = QVBoxLayout()
        buttons_horizontal_layout = QHBoxLayout()

        encrypt_button = QPushButton("Encrypt")
        decrypt_button = QPushButton("Decrypt")
        refresh_keys_button = QPushButton("Refresh keys")
        encrypt_button.clicked.connect(self.encrypt_button_clicked)
        decrypt_button.clicked.connect(self.decrypt_button_clicked)
        refresh_keys_button.clicked.connect(self.analyze_text_for_substitution_cipher)
        buttons_horizontal_layout.addWidget(encrypt_button)
        buttons_horizontal_layout.addWidget(decrypt_button)
        buttons_horizontal_layout.addWidget(refresh_keys_button)

        self.cipher_key_layout.addLayout(buttons_horizontal_layout)

        key_label = QLabel('Keys')
        self.cipher_key_layout.addWidget(key_label)
        vertical_layout_keys = QVBoxLayout()
        if self.cipher_type == self.ROT_CIPHER:
            rot_key_size_input = QSpinBox()
            rot_key_size_input.setSingleStep(1)
            rot_key_size_input.setRange(self.ROT_KEY_SIZE_MIN, self.ROT_KEY_SIZE_MAX)
            rot_key_size_input.setValue(self.rot_key_size)
            rot_key_size_input.valueChanged.connect(lambda x: setattr(self, 'rot_key_size', x))

            vertical_layout_keys.addWidget(rot_key_size_input)
        elif self.cipher_type == self.SUBSTITUTION_CIPHER:
            self.substitution_keys_line_edit = QLineEdit()
            self.substitution_values_line_edit = QLineEdit()
            self.substitution_values_line_edit.textChanged.connect(self.handle_substitution_values_line_edit_changed)
            vertical_layout_keys.addWidget(self.substitution_keys_line_edit)
            vertical_layout_keys.addWidget(self.substitution_values_line_edit)

            # if there is plain_text get all characters as key
            self.analyze_text_for_substitution_cipher()

            # skip symbols area
            skip_symbols_layout = QHBoxLayout()

            skip_symbols_layout.addWidget(QLabel('Skip Symbols:'))
            skip_symbols_white_spaces = QCheckBox(self.WHITESPACES)
            skip_symbols_white_spaces.setChecked(self.WHITESPACES in self.skip_symbols)
            skip_symbols_white_spaces.stateChanged.connect(
                lambda: self.skip_symbols_checkbox(skip_symbols_white_spaces)
            )

            skip_symbols_white_punctuation = QCheckBox(self.PUNCTUATION)
            skip_symbols_white_punctuation.setChecked(self.PUNCTUATION in self.skip_symbols)
            skip_symbols_white_punctuation.stateChanged.connect(
                lambda: self.skip_symbols_checkbox(skip_symbols_white_punctuation)
            )

            skip_symbols_white_digits = QCheckBox(self.DIGITS)
            skip_symbols_white_digits.setChecked(self.DIGITS in self.skip_symbols)
            skip_symbols_white_digits.stateChanged.connect(
                lambda: self.skip_symbols_checkbox(skip_symbols_white_digits)
            )

            skip_symbols_layout.addWidget(skip_symbols_white_spaces)
            skip_symbols_layout.addWidget(skip_symbols_white_punctuation)
            skip_symbols_layout.addWidget(skip_symbols_white_digits)
            vertical_layout_keys.addLayout(skip_symbols_layout)

        self.cipher_key_layout.addLayout(vertical_layout_keys)
        self.cipher_tab.layout().addLayout(self.cipher_key_layout, 1, 0)

    def handle_substitution_values_line_edit_changed(self):
        self.substitution_cipher_values = self.substitution_values_line_edit.text()

    def _remove_layout_and_widgets(self, layout, delete_parent_layout=False):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if isinstance(item, QLayout):
                self._remove_layout_and_widgets(item, True)
            else:
                item.widget().setParent(None)
        if delete_parent_layout:
            layout.deleteLater()

    def analyze_sample_text_button_clicked(self):
        sample_text = self.sample_text_text_edit.toPlainText().upper()
        self.sample_text_text_edit.setPlainText(sample_text)
        sample_text_frequency = chr_frequency(sample_text, skip_symbols=string.whitespace + string.punctuation)
        self.sample_text_frequency_chart.update_data(
            sample_text_frequency.keys(), sample_text_frequency.values()
        )
        self.is_sample_text_analyzed = bool(sample_text_frequency)
        self.tabs.setTabEnabled(3, self.is_sample_text_analyzed)

    def list_top_words_button_clicked(self, top_words_list_box, textedit):
        # delete items in list
        while top_words_list_box.count():
            top_words_list_box.takeItem(0)  # pop first item until no item left

        sample_text = textedit.toPlainText().upper()
        top_words = get_top_n_letter_words(sample_text, top=self.top_words_count,
                                           number_of_letters=self.top_words_letters)

        # add items to list
        for i, word in enumerate(top_words.items()):
            top_words_list_box.insertItem(i, f"{word[0]} [{word[1]} occurrence]")

        if textedit == self.decipher_text_text_edit:
            # open word substitution menu
            self.show_substitution_menu(top_words)

    def show_substitution_menu(self, top_words):
        self.substitution_words_line_edits = ([], [],)
        self._remove_layout_and_widgets(self.substitute_words_layout)
        for i, word in enumerate(top_words.keys()):
            word_lineedit = QLineEdit()
            word_lineedit.setText(word)
            substitute_word_lineedit = QLineEdit()
            substitute_word_lineedit.setText(word)

            # populate line edits
            self.substitution_words_line_edits[0].append(word_lineedit)
            self.substitution_words_line_edits[1].append(substitute_word_lineedit)

            self.substitute_words_layout.addWidget(word_lineedit, i, 0)
            self.substitute_words_layout.addWidget(substitute_word_lineedit, i, 1)

        self.substitute_words_button.setDisabled(not self.substitution_words_line_edits[0])

    def substitute_words_button_clicked(self):
        word_pairs = []
        for word_line_edit, substitution_word_line_edit in zip(*self.substitution_words_line_edits):
            word_pairs.append((word_line_edit.text(), substitution_word_line_edit.text()))
        for s, t in word_pairs:
            self.crack_keys = substitute_word_as(s, t, self.crack_keys)
        self.crack_button_clicked()

    def cipher_radio_button_clicked(self):
        radio_button = self.sender()
        if radio_button.isChecked():
            self.cipher_type = radio_button.cipher
            self._remove_layout_and_widgets(self.cipher_key_layout, True)
            self._construct_key_entry()

    def upper_case_plain_text(self):
        self.plain_text = self.plain_text.upper()
        self.plain_text_text_edit.setPlainText(self.plain_text)

    def encrypt_button_clicked(self):
        self.upper_case_plain_text()
        if self.cipher_type == self.ROT_CIPHER:
            cipher_text_generator = rot_n_generator(self.plain_text_text_edit.toPlainText(), self.rot_key_size)
            self.cipher_text_text_edit.setText(''.join(cipher_text_generator))
        elif self.cipher_type == self.SUBSTITUTION_CIPHER:
            char_mapping = {k: v for k, v in zip(self.substitution_cipher_keys, self.substitution_cipher_values)}
            cipher_text = substitution_cipher(self.plain_text_text_edit.toPlainText(), char_mapping)
            self.cipher_text_text_edit.setPlainText(cipher_text)

        else:
            raise NotImplementedError

    def decrypt_button_clicked(self):
        if self.cipher_type == self.ROT_CIPHER:
            cipher_text_generator = rot_n_generator(self.cipher_text_text_edit.toPlainText(), self.rot_key_size,
                                                    decrypt=True)
            self.plain_text_text_edit.setText(''.join(cipher_text_generator))
        elif self.cipher_type == self.SUBSTITUTION_CIPHER:
            char_mapping = {k: v for k, v in zip(self.substitution_cipher_values, self.substitution_cipher_keys)}
            cipher_text = substitution_cipher(self.cipher_text_text_edit.toPlainText(), char_mapping)
            self.plain_text_text_edit.setPlainText(cipher_text)
        else:
            raise NotImplementedError

    def analyze_text_for_substitution_cipher(self):
        plain_text = self.plain_text_text_edit.toPlainText().upper()
        if not plain_text or self.cipher_type != self.SUBSTITUTION_CIPHER:
            return
        skip = ''.join(map(lambda i: getattr(string, i), self.skip_symbols))
        self.plain_text_freq = chr_frequency(plain_text, skip_symbols=skip)
        self.substitution_cipher_keys = ''.join(self.plain_text_freq.keys())
        self.substitution_cipher_values = random_shuffle_str(self.substitution_cipher_keys)
        self.substitution_values_line_edit.setText(self.substitution_cipher_values)
        self.substitution_keys_line_edit.setText(self.substitution_cipher_keys)

    def skip_symbols_checkbox(self, checkbox):
        if not checkbox.isChecked():
            self.skip_symbols.remove(checkbox.text())
        else:
            self.skip_symbols.append(checkbox.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CipherTextAnalysis()
    window.setWindowTitle('Substitution Cipher - Character Analysis')
    window.setWindowIcon(QtGui.QIcon('icon.png'))
    window.setFixedSize(window.WINDOW_W, window.WINDOW_H)
    window.show()
    sys.exit(app.exec_())
