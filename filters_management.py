from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QComboBox,
    QPushButton, QGroupBox, QFormLayout, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

class FiltersManagementWindow(QWidget):
    windowClosed = pyqtSignal()
    
    def __init__(self, main_window=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowTitleHint)
        self.main_window = main_window
        self.initUI()
        self.setMinimumSize(400, 300)

    def initUI(self):
        self.setWindowTitle("Управление фильтрами")
        self.setWindowIcon(QIcon(self.main_window.set_logo()))
        self.load_data_from_db()
        self.set_ui()

    def set_ui(self):
        main_content = QVBoxLayout()
        self.setLayout(main_content)

        # Группа для типов (только отображение)
        const_filters_group = QGroupBox("Фиксированные фильтры")
        form_property_const_layout = QFormLayout()

        property_type_combo = QComboBox()
        property_type_combo.addItems(self.property_categories)
        form_property_const_layout.addRow("Типы размещения:", property_type_combo)

        booking_status_checkboxes = {"С активными бронями", "Без активных броней"}
        booking_status_combo = QComboBox()
        booking_status_combo.addItems(booking_status_checkboxes)
        form_property_const_layout.addRow("Статусы бронирования:", booking_status_combo)

        const_filters_group.setLayout(form_property_const_layout)

        # Группа для удобств (полное управление)
        amenities_group = QGroupBox("Управление удобствами")
        self.form_amenities_layout = QFormLayout()
        
        self.amenities_combo = QComboBox()
        self.amenities_combo.addItems(self.amenities)
        self.title_amenities_edit = QLineEdit()
        
        # Кнопки управления
        self.btn_add_amenity = QPushButton("Добавить")
        self.btn_edit_amenity = QPushButton("Изменить")
        self.btn_remove_amenity = QPushButton("Удалить")
        
        self.btn_add_amenity.clicked.connect(self.add_amenity)
        self.btn_edit_amenity.clicked.connect(self.edit_amenity)
        self.btn_remove_amenity.clicked.connect(self.remove_amenity)

        # Компоновка
        self.form_amenities_layout.addRow("Список:", self.amenities_combo)
        self.form_amenities_layout.addRow("Название:", self.title_amenities_edit)
        self.form_amenities_layout.addRow(self.btn_add_amenity)
        self.form_amenities_layout.addRow(self.btn_edit_amenity)
        self.form_amenities_layout.addRow(self.btn_remove_amenity)
        amenities_group.setLayout(self.form_amenities_layout)

        main_content.addWidget(const_filters_group)
        main_content.addWidget(amenities_group)

    def load_data_from_db(self):
        try:
            self.property_categories = self.main_window.db.get_property_categories()
            self.amenities = self.main_window.db.get_amenities()
        except Exception as e:
            print(str(e))
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки загрузки данных из базы данных")
            self.close()

    # Методы только для удобств
    def add_amenity(self):
        title = self.title_amenities_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите название удобства")
            return
            
        if title in self.amenities:
            QMessageBox.warning(self, "Ошибка", "Удобство уже существует")
            return

        try:
            self.main_window.db.execute_query(
                "INSERT INTO amenity (name) VALUES (%s)", 
                (title,)
            )
            QMessageBox.information(self, "Успех", "Удобство добавлено!")
            self.update_amenities_ui()
        except Exception as e:
            print(str(e))
            QMessageBox.critical(self, "Ошибка", "Ошибка при добавлении удобства")

    def edit_amenity(self):
        old_title = self.amenities_combo.currentText()
        new_title = self.title_amenities_edit.text().strip()

        if not new_title:
            QMessageBox.warning(self, "Ошибка", "Введите новое название")
            return

        try:
            self.main_window.db.execute_query(
                "UPDATE amenity SET name = %s WHERE name = %s",
                (new_title, old_title)
            )
            QMessageBox.information(self, "Успех", "Удобство изменено!")
            self.update_amenities_ui()
        except Exception as e:
            print(str(e))
            QMessageBox.critical(self, "Ошибка", "Ошибка при редактировании удобства")

    def remove_amenity(self):
        title = self.amenities_combo.currentText()
        
        confirm = QMessageBox(
            QMessageBox.Icon.Question,
            "Подтверждение", 
            f"Удалить удобство '{title}'?\nВсе связанные данные будут потеряны!",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            parent=self
        )
        
        yes_button = confirm.button(QMessageBox.StandardButton.Yes)
        yes_button.setText("Да")

        no_button = confirm.button(QMessageBox.StandardButton.No)
        no_button.setText("Нет")
        
        if confirm.exec() == QMessageBox.StandardButton.Yes:
            try:
                self.main_window.db.execute_query(
                    "DELETE FROM amenity WHERE name = %s",
                    (title,))
                QMessageBox.information(self, "Успех", "Удобство удалено!")
                self.update_amenities_ui()
            except Exception as e:
                print(str(e))
                QMessageBox.critical(self, "Ошибка", "Ошибка при удалении удобства")

    def update_amenities_ui(self):
        self.amenities = self.main_window.db.get_amenities()
        self.amenities_combo.clear()
        self.amenities_combo.addItems(self.amenities)
        self.title_amenities_edit.clear()
        self.main_window.amenities_scroll_layout()

    def closeEvent(self, event):
        self.windowClosed.emit()
        self.main_window.setEnabled(True)
        self.main_window.load_data_from_db()
        self.main_window.amenities_scroll_layout()
        self.main_window.search_property()
        event.accept()