from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QLabel,
    QPushButton, QGroupBox, QFormLayout, QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

class SettingsWindow(QWidget):
    windowClosed = pyqtSignal()
    
    def __init__(self, main_window=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowTitleHint)
        self.main_window = main_window
        self.initUI()
        self.setMinimumSize(500, 500)

    def initUI(self):
        self.setWindowTitle("Настройки базы данных")
        self.setWindowIcon(QIcon(self.main_window.set_logo()))
        self.set_ui()

    def set_ui(self):
        settings_main_content = QVBoxLayout() 
        self.setLayout(settings_main_content)

        self.btn_show_pass = QPushButton("Показать пароли")
        self.btn_show_pass.setCheckable(True)

        connect_settings_group = QGroupBox("Подключение БД")
        change_settings_group = QGroupBox("Изменение параметров БД")
        info_settings_group = QGroupBox("Информация о подключенной БД")

        self.form_connect_settings_layout = QFormLayout()
        self.form_change_settings_layout = QFormLayout()
        self.form_info_settings_layout = QFormLayout()

        #Подлючение бд
        self.user_bd = QLineEdit()
        self.password_bd = QLineEdit()
        self.host_bd = QLineEdit()
        self.port_bd = QLineEdit()
        self.database_name = QLineEdit()

        self.form_connect_settings_layout.addRow("Пользователь:", self.user_bd)
        self.form_connect_settings_layout.addRow("Пароль:", self.password_bd)
        self.form_connect_settings_layout.addRow("Имя/адрес хоста:", self.host_bd)
        self.form_connect_settings_layout.addRow("Порт:", self.port_bd)
        self.form_connect_settings_layout.addRow("База данных:", self.database_name)

        self.btn_connect_bd = QPushButton("Подключить базу данных")
        self.btn_connect_bd.clicked.connect(self.connect_bd)

        self.form_connect_settings_layout.addWidget(self.btn_connect_bd)
        connect_settings_group.setLayout(self.form_connect_settings_layout)

        self.get_bd_config()

        #Измнение бд
        self.ch_user_bd = QLineEdit(self.user)
        self.ch_password_bd = QLineEdit(self.password)
        self.ch_password_bd.setEchoMode(QLineEdit.EchoMode.Password)
        self.ch_host_bd = QLineEdit(self.host)
        self.ch_port_bd = QLineEdit(self.port)
        self.ch_database_name = QLineEdit(self.database)

        self.form_change_settings_layout.addRow("Пользователь:", self.ch_user_bd)
        self.form_change_settings_layout.addRow("Пароль:", self.ch_password_bd)
        self.form_change_settings_layout.addRow("Имя/адрес хоста:", self.ch_host_bd)
        self.form_change_settings_layout.addRow("Порт:", self.ch_port_bd)
        self.form_change_settings_layout.addRow("База данных:", self.ch_database_name)

        self.btn_change_bd = QPushButton("Применить изменения")
        self.btn_change_bd.clicked.connect(self.change_settings_bd)

        self.form_change_settings_layout.addWidget(self.btn_change_bd)
        change_settings_group.setLayout(self.form_change_settings_layout)

        #Информация о бд
        self.user_label = QLabel(self.user)
        self.password_label = QLabel("********")
        self.host_label = QLabel(self.host)
        self.port_label = QLabel(self.port)
        self.database_label = QLabel(self.database)

        self.form_info_settings_layout.addRow("Пользователь:", self.user_label)
        self.form_info_settings_layout.addRow("Пароль:", self.password_label)
        self.form_info_settings_layout.addRow("Имя/адрес хоста:", self.host_label)
        self.form_info_settings_layout.addRow("Порт:", self.port_label)
        self.form_info_settings_layout.addRow("База данных:", self.database_label)

        info_settings_group.setLayout(self.form_info_settings_layout)

        settings_main_content.addWidget(self.btn_show_pass)
        settings_main_content.addWidget(info_settings_group)
        settings_main_content.addWidget(connect_settings_group)
        settings_main_content.addWidget(change_settings_group)

        self.btn_show_pass.clicked.connect(self.show_pass)

    def show_pass(self):
        if self.btn_show_pass.isChecked():
            self.ch_password_bd.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_label.setText(self.password)
            self.btn_show_pass.setText("Скрыть пароли")
        else:
            self.ch_password_bd.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_label.setText("********")
            self.btn_show_pass.setText("Показать пароли")

    def clear_qlineedit(self):
        self.user_bd.clear()
        self.password_bd.clear()
        self.host_bd.clear()
        self.port_bd.clear()
        self.database_name.clear()
        
        self.ch_user_bd.clear()
        self.ch_password_bd.clear()
        self.ch_host_bd.clear()
        self.ch_port_bd.clear()
        self.ch_database_name.clear()

    def set_info_config(self):
        self.get_bd_config()
        self.ch_user_bd.setText(self.user)
        self.ch_password_bd.setText(self.password)
        self.ch_host_bd.setText(self.host)
        self.ch_port_bd.setText(self.port)
        self.ch_database_name.setText(self.database)

        self.user_label.setText(self.user)
        self.password_label.setText(self.password)
        self.host_label.setText(self.host)
        self.port_label.setText(self.port)
        self.database_label.setText(self.database)
        self.show_pass()

    def get_bd_config(self):
        self.config_bd = self.main_window.db.get_config()
        self.user = self.config_bd['user']
        self.password = self.config_bd['password']
        self.host = self.config_bd['host']
        self.port = self.config_bd['port']
        self.database = self.config_bd['database']

    def connect_bd(self):
        self.con_config = {
            "user": self.user_bd.text(),
            "password": self.password_bd.text(),
            "host": self.host_bd.text(),
            "port": self.port_bd.text(),
            "database": self.database_name.text()
        }

        connect_success = self.main_window.db.set_config(self.user_bd.text(), self.password_bd.text(), self.host_bd.text(), 
                                                        self.port_bd.text(), self.database_name.text())
        if connect_success:
            QMessageBox.information(self, "Успех", "Подключение к базе данных прошло успешно!")
            try:
                self.main_window.update_property_list()
                self.main_window.load_data_from_db()
            except:
                QMessageBox.critical(self, "Ошибка", "Ошибка при загрузки данных из базы!\nИспользуется база данных по умолчанию.")
                self.main_window.db.set_default_bg()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к базе данных!\nИспользуется база данных по умолчанию.")
            self.main_window.db.set_default_bg()

        self.clear_qlineedit()
        self.set_info_config()

    def change_settings_bd(self):
        self.ch_config = {
            "user": self.ch_user_bd.text(),
            "password": self.ch_password_bd.text(),
            "host": self.ch_host_bd.text(),
            "port": self.ch_port_bd.text(),
            "database": self.ch_database_name.text()
        }
        connect_success = self.main_window.db.set_config(self.ch_user_bd.text(), self.ch_password_bd.text(), 
                                                        self.ch_host_bd.text(), self.ch_port_bd.text(), self.ch_database_name.text())
        if connect_success:
            QMessageBox.information(self, "Успех", "Подключение к базе данных прошло успешно!")
            try:
                self.main_window.update_property_list()
                self.main_window.load_data_from_db()
            except:
                QMessageBox.critical(self, "Ошибка", "Ошибка при загрузки данных из базы!\nИспользуется база данных по умолчанию.")
                self.main_window.db.set_default_bg()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к базе данных!\nИспользуется база данных по умолчанию.")
            self.main_window.db.set_default_bg()

        self.clear_qlineedit()
        self.set_info_config()

    def closeEvent(self, event):
        self.windowClosed.emit()
        self.main_window.setEnabled(True)
        self.clear_qlineedit()
        self.set_info_config()
        event.accept()