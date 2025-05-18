from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QComboBox, QSpinBox, QGridLayout,
    QPushButton, QGroupBox, QLineEdit, QFormLayout, QTextEdit, QCheckBox, 
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

class PropertyManagementWindow(QWidget):
    windowClosed = pyqtSignal()
    
    def __init__(self, main_window=None, property_data=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowTitleHint)
        self.setMinimumSize(600, 400)
        self.main_window = main_window
        self.property_data = property_data
        self.initUI()
        
        if property_data:  # Режим редактирования
            self.load_existing_data()
            self.append_property.hide()
            self.details_group.setTitle("Редактирование недвижимости")
        else:  # Режим добавления
            self.save_changes_property.hide()
            self.btn_cancellation.hide()
            self.details_group.setTitle("Добавление недвижимости")

            self.clear_fields()

    def initUI(self):
        self.setWindowTitle("Управление недвижимостью")
        self.setWindowIcon(QIcon(self.main_window.set_logo()))
        # Загрузка данных из БД
        self.load_data_from_db()
        self.create_ui_elements()

    def closeEvent(self, event):
        self.windowClosed.emit()
        self.main_window.setEnabled(True)
        event.accept()

    def load_data_from_db(self):
        # Загрузка категорий
        self.property_categories = self.main_window.db.get_property_categories()
        if not self.property_categories:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить категории")
            self.close()

        # Загрузка удобств
        self.amenities = self.main_window.db.get_amenities()
        if not self.amenities:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список удобств")
            return
        
    def create_ui_elements(self):
        man_main_content = QVBoxLayout() 
        self.setLayout(man_main_content)

        self.details_group = QGroupBox("Добавление недвижимости")
        form_layout = QFormLayout()

        #Название
        self.title = QLineEdit()
        self.title.setMaxLength(100)
        self.title.setPlaceholderText("Максимум 100 символов")

        #Тип недвижимости
        self.property_type = QComboBox()
        self.property_type.addItems(self.property_categories)

        #Местоположение
        self.address = QLineEdit()
        self.address.setMaxLength(200)
        self.address.setPlaceholderText("Максимум 200 символов")

        #Описание
        self.description = QTextEdit()

        #Удобства
        self.amenity_checkboxes = {}
        amenities_layout = QGridLayout()
        
        for i, amenity_name in enumerate(self.amenities):
            checkbox = QCheckBox(amenity_name)
            self.amenity_checkboxes[amenity_name] = checkbox
            row = i // 2
            col = i % 2
            amenities_layout.addWidget(checkbox, row, col)

        #Цена за ночь
        self.price_per_night = QSpinBox()
        self.price_per_night.setMinimum(0)
        self.price_per_night.setMaximum(2147483647)
        self.price_per_night.setPrefix("₽ ")

        form_layout.addRow("Название:", self.title)
        form_layout.addRow("Тип размещения:", self.property_type)
        form_layout.addRow("Местоположение:", self.address)
        form_layout.addRow("Описание:", self.description)
        form_layout.addRow("Удобства:", amenities_layout)
        form_layout.addRow("Цена за ночь:", self.price_per_night)

        self.append_property = QPushButton("Добавить недвижимость")
        self.append_property.setFixedHeight(30)
        self.append_property.clicked.connect(self.publish_property)

        self.save_changes_property = QPushButton("Сохранить")
        self.save_changes_property.setFixedHeight(30)
        self.save_changes_property.clicked.connect(self.update_property)

        self.btn_cancellation = QPushButton("Отмена")
        self.btn_cancellation.setFixedHeight(30)
        self.btn_cancellation.clicked.connect(self.cancellation_change_property)

        self.details_group.setLayout(form_layout)
        
        man_main_content.addWidget(self.details_group)
        man_main_content.addWidget(self.append_property, alignment=Qt.AlignmentFlag.AlignBottom)
        man_main_content.addWidget(self.save_changes_property, alignment=Qt.AlignmentFlag.AlignBottom)
        man_main_content.addWidget(self.btn_cancellation, alignment=Qt.AlignmentFlag.AlignBottom)

    def cancellation_change_property(self):
        confirm_cancel = QMessageBox(
            QMessageBox.Icon.Question,
            "Отмена изменений",
            "Вы уверены, что хотите отменить внесенные изменения?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            parent=self
        )

        yes_button = confirm_cancel.button(QMessageBox.StandardButton.Yes)
        yes_button.setText("Да")

        no_button = confirm_cancel.button(QMessageBox.StandardButton.No)
        no_button.setText("Нет")

        if confirm_cancel.exec() == QMessageBox.StandardButton.Yes:
            self.close()

    def publish_property(self):
        # Получаем выбранные удобства
        self.selected_amenities = [name for name, cb in self.amenity_checkboxes.items() if cb.isChecked()]
        
        # Формируем данные для вставки
        property_data = {
            'title': self.title.text(),
            'property_type': self.property_type.currentText(),
            'address': self.address.text(),
            'description': self.description.toPlainText(),
            'price': self.price_per_night.value(),
            'amenities': self.selected_amenities,
        }
        
        if self.property_data:
            self.update_property()
        else:
            if self.save_property(property_data):
                QMessageBox.information(self, "Успех", "Недвижимость добавлена!")
            else:
                QMessageBox.warning(self, "Неудача", "Не удалось добавить недвижимость")
            
        self.main_window.search_property()
        self.close()


    def save_property(self, data: dict) -> bool:
        try:
            query = """
                INSERT INTO property 
                (title, description, address, price_per_night, property_type)
                VALUES (%s, %s, %s, %s, %s::property_category)
                RETURNING property_id
            """
            result = self.main_window.db.execute_query(
                query,
                (
                    data['title'],
                    data['description'],
                    data['address'],
                    data['price'],
                    data['property_type'],
                ),
                fetch=True
            )
            
            if not result:
                return False

            property_id = result[0]['property_id']

            # Вставляем удобства
            if data['amenities']:
                amenity_query = """
                    INSERT INTO property_amenity (property_id, amenity_id)
                    SELECT %s, amenity_id FROM amenity WHERE name = ANY(%s)
                """
                self.main_window.db.execute_query(
                    amenity_query,
                    (property_id, data['amenities'])
                )

            return True
        
        except Exception as e:
            print(f"Ошибка при сохранении недвижимости: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении недвижимости")
            return False
        
    def clear_fields(self):
        self.title.clear()
        self.address.clear()
        self.description.clear()
        self.price_per_night.setValue(0)
        self.property_type.setCurrentIndex(0)
        for cb in self.amenity_checkboxes.values():
            cb.setChecked(False)

    def load_existing_data(self):
        self.title.setText(self.property_data['title'])
        self.address.setText(self.property_data['address'])
        self.description.setPlainText(self.property_data['description'])
        self.price_per_night.setValue(self.property_data['price_per_night'])
        
        index = self.property_type.findText(self.property_data['property_type'])
        if index >= 0:
            self.property_type.setCurrentIndex(index)
        
        for amenity in self.property_data['amenities']:
            if amenity in self.amenity_checkboxes:
                self.amenity_checkboxes[amenity].setChecked(True)

    def remove_property(self, property_data):
        confirm = QMessageBox(
            QMessageBox.Icon.Question,
            "Удаление",
            f"Удалить объект '{property_data['title']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            parent=self
        )

        yes_button = confirm.button(QMessageBox.StandardButton.Yes)
        yes_button.setText("Да")

        no_button = confirm.button(QMessageBox.StandardButton.No)
        no_button.setText("Нет")
        
        if confirm.exec() == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute_query(
                    "DELETE FROM property WHERE property_id = %s",
                    (property_data['property_id'],)
                )
                QMessageBox.information(self, "Успех", "Недвижимость успешно удалена")
                self.main_window.search_property()
            except Exception as e:
                print(str(e))
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления недвижимости")

    def update_property(self):
        try:
            self.selected_amenities = [name for name, cb in self.amenity_checkboxes.items() if cb.isChecked()]
            # Получаем данные из полей
            new_data = {
                'title': self.title.text(),
                'property_type': self.property_type.currentText(),
                'address': self.address.text(),
                'description': self.description.toPlainText(),
                'price': self.price_per_night.value(),
                'amenities': self.selected_amenities,
            }
            
            # SQL-запрос для обновления
            query = """
                UPDATE property SET
                    title = %s,
                    address = %s,
                    description = %s,
                    price_per_night = %s,
                    property_type = %s::property_category
                WHERE property_id = %s
            """
            self.main_window.db.execute_query(
                query,
                (
                    new_data['title'],
                    new_data['address'],
                    new_data['description'],
                    new_data['price'],
                    new_data['property_type'],
                    self.property_data['property_id']
                )
            )

            delete_query = "DELETE FROM property_amenity WHERE property_id = %s"
            self.main_window.db.execute_query(
                delete_query, 
                (self.property_data['property_id'],)
            )

            if new_data['amenities']:
                insert_query = """
                    INSERT INTO property_amenity (property_id, amenity_id)
                    SELECT %s, amenity_id FROM amenity WHERE name = ANY(%s::text[])
                """
                self.main_window.db.execute_query(
                    insert_query,
                    (self.property_data['property_id'], new_data['amenities'])
                )
                
            QMessageBox.information(self, "Успех", "Изменения недвижимости успешно применены!")
            self.main_window.search_property()
            self.close()

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка обновления недвижимости")

    def update_property_list(self):
        self.main_window.search_property()