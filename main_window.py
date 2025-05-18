import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QSizePolicy, QGridLayout,
    QPushButton, QLabel, QGroupBox, QScrollArea, QFormLayout, QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

from database import DatabaseManager
from settings_bd import SettingsWindow
from property_management import PropertyManagementWindow
from booking_management import BookingManagementWindow
from filters_management import FiltersManagementWindow

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        if not self.db.connect():
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к базе данных")
            sys.exit(1)
        self.user_data = None
        self.load_data_from_db()
        self.initUI()
        self.setMinimumSize(1200, 700)
        
        self.settings_bd = SettingsWindow(main_window=self)
        self.filters_management = FiltersManagementWindow(main_window=self)

    def activate_window(self):
        self.setEnabled(True)
        self.raise_()
        self.activateWindow()

    def set_logo(self):
        path_logo = "icon_white_black.png"
        return path_logo

    def initUI(self):
        self.setWindowTitle("SmartBooking")
        self.setWindowIcon(QIcon(self.set_logo()))
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Верхняя панель
        self.header_panel = QVBoxLayout()
        self.header_group = QGroupBox()
        header_panel_in_group = QHBoxLayout()
        header_layout_name = QHBoxLayout()
        header_layout_btn = QHBoxLayout()
        
        self.name_label = QLabel("SmartBooking")
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.logo = QLabel()
        pixmap = QPixmap(self.set_logo())
        self.logo.setPixmap(pixmap)
        self.logo.setScaledContents(True)
        self.logo.setFixedSize(30,30)
        self.about_button = QPushButton("Справка")
        self.about_button.setFixedSize(70, 30)
        self.btn_admin_settings_bd = QPushButton("Настройки БД")
        self.btn_admin_settings_bd.setFixedSize(100, 30)
        
        header_layout_name.addWidget(self.logo)
        header_layout_name.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout_btn.addWidget(self.btn_admin_settings_bd, alignment=Qt.AlignmentFlag.AlignRight)
        header_layout_btn.addWidget(self.about_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        header_panel_in_group.addLayout(header_layout_name, 90)
        header_panel_in_group.addLayout(header_layout_btn, 10)

        self.header_group.setLayout(header_panel_in_group)
        self.header_panel.addWidget(self.header_group)

        # Основной контент
        content_layout = QHBoxLayout()
        
        # Левая панель (фильтры)
        self.filter_group = QGroupBox("Фильтры")
        self.active_text = "С активными бронями"
        self.inactive_text = "Без активных броней"
        self.amenities_scroll_layout()
        
        # Правая панель (недвижимость)
        self.property_group = QGroupBox("Недвижимость")
        property_content_in_group = QVBoxLayout()
        property_host_btn_layout = QHBoxLayout()
        property_searchbar_layout = QHBoxLayout()
        self.property_list_layout = QVBoxLayout()

        property_content_in_group.addLayout(property_searchbar_layout)
        property_content_in_group.addLayout(property_host_btn_layout)
        property_content_in_group.addLayout(self.property_list_layout)

        #Поиск
        self.property_searchbar = QLineEdit()
        self.property_searchbar.setPlaceholderText("🔍 Поиск по названию...")
        self.property_searchbar.setMaxLength(100)
        self.btn_search = QPushButton("Найти")

        property_searchbar_layout.addWidget(self.property_searchbar, 80)
        property_searchbar_layout.addWidget(self.btn_search, 20)

        self.btn_add_property = QPushButton("Добавить недвижимость")
        property_host_btn_layout.addWidget(self.btn_add_property, alignment=Qt.AlignmentFlag.AlignTop)

        self.property_group.setLayout(property_content_in_group)

        self.search_property()

        content_layout.addWidget(self.filter_group, 30)
        content_layout.addWidget(self.property_group, 70)

        main_layout.addLayout(self.header_panel, 10)
        main_layout.addLayout(content_layout, 90)
        
        self.about_button.clicked.connect(self.show_about)
        self.btn_admin_settings_bd.clicked.connect(self.show_settings_bd)
        self.btn_add_property.clicked.connect(self.add_property)
        self.btn_search.clicked.connect(self.filter_search)
        self.property_searchbar.returnPressed.connect(self.filter_search)

    def show_about(self):
        about_text = """SmartBooking - информационная система онлайн бронирования недвижимости
\nО программе: 
Автор: студент Машнев М.О. группа бИВТ231
Версия: 1.2
"""
        QMessageBox.information(self, "Справка", about_text)

    def show_settings_bd(self):
        self.settings_bd.show()
        self.setEnabled(False)

    def management_property(self, property_data=None):
        self.property_management = PropertyManagementWindow(
            main_window=self,
            property_data=property_data
        )

    def management_filters(self):
        self.filters_management.show()
        self.setEnabled(False)

    def add_property(self):
        self.management_property()
        self.property_management.clear_fields()
        self.property_management.show()
        self.setEnabled(False)

    def edit_property(self, property_data):
        self.management_property(property_data=property_data)
        self.property_management.show()
        self.setEnabled(False)

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
                self.search_property()
            except Exception as e:
                print(str(e))
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления недвижимости")


    def rent_property(self, property_data):
        self.booking_management = BookingManagementWindow(
            main_window=self,
            property_data=property_data
        )
        self.booking_management.show()
        self.setEnabled(False)

    def amenities_scroll_layout(self):
        if not self.filter_group.layout():
            self.filter_group.setLayout(QVBoxLayout())
        else:
            while self.filter_group.layout().count() > 0:
                item = self.filter_group.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)

        self.load_data_from_db()
        
        btn_management = QPushButton("Управление фильтрами")
        btn_management.clicked.connect(self.management_filters)
        main_layout.addWidget(btn_management)

        main_layout.addLayout(self.create_category_filters())
        main_layout.addLayout(self.create_status_filters())
        main_layout.addWidget(self.create_amenities_filters())
        main_layout.addLayout(self.create_filter_buttons())

        self.filter_group.layout().addWidget(main_container)

    def create_category_filters(self):
        layout = QVBoxLayout()
        head = QLabel("Тип размещения")
        head.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(head)        
        
        self.categories_checkboxes = {}
        for category in self.property_categories:
            cb = QCheckBox(category)
            self.categories_checkboxes[category] = cb
            layout.addWidget(cb)
        
        return layout

    def create_amenities_filters(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        
        head = QLabel("Удобства")
        head.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        grid = QGridLayout(content)
        
        self.amenity_checkboxes = {}
        for i, amenity in enumerate(self.amenities):
            cb = QCheckBox(amenity)
            self.amenity_checkboxes[amenity] = cb
            row, col = i // 2, i % 2
            grid.addWidget(cb, row, col)
        
        grid.setRowStretch(grid.rowCount(), 1)
        scroll.setWidget(content)

        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QWidget#scroll_widget {
                background: transparent;
            }
        """)
        
        layout.addWidget(head)
        layout.addWidget(scroll)
        return container

    def create_status_filters(self):
        layout = QVBoxLayout()
        head = QLabel("Статус бронирования")
        head.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(head)
        
        self.booking_status_checkboxes = {}
        for status in [self.active_text, self.inactive_text]:
            cb = QCheckBox(status)
            self.booking_status_checkboxes[status] = cb
            layout.addWidget(cb)
        
        return layout

    def create_filter_buttons(self):
        layout = QVBoxLayout()
        btn_apply = QPushButton("Применить")
        btn_apply.clicked.connect(self.filter_search)
        
        btn_reset = QPushButton("Сбросить")
        btn_reset.clicked.connect(self.reset_filters)
        
        layout.addWidget(btn_apply)
        layout.addWidget(btn_reset)
        return layout

    def scroll_list_property(self, properties: list):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout()
        content.setLayout(content_layout)

        if not properties:
            no_results = QLabel("К сожалению, ничего не найдено по вашему запросу. \nПопробуйте изменить параметры поиска.")
            no_results.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            content_layout.addWidget(no_results)
        else:
            for prop in properties:
                group = QGroupBox()
                layout = QFormLayout()
                
                title = QLabel(prop['title'])
                address = QLabel(prop['address'])
                description = QLabel(prop['description'])
                description.setWordWrap(True)
                description.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                description.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Preferred
                )
                description.setMaximumHeight(100)

                amenities_container = QWidget()
                amenities_layout = QHBoxLayout(amenities_container)
                amenities = QLabel(", ".join(prop['amenities']) if prop['amenities'][0] else "Нет удобств")
                amenities.setWordWrap(True)
                amenities.setAlignment(Qt.AlignmentFlag.AlignJustify)
                amenities_layout.addWidget(amenities)
                
                price = QLabel(f"{int(prop['price_per_night'])} ₽/ночь")
                
                layout.addRow("Название:", title)
                layout.addRow("Адрес:", address)
                description_widget = self.create_description_widget(prop['description'])
                layout.addRow("Описание:", description_widget)
                layout.addRow("Удобства:", amenities_container)
                layout.addRow("Цена:", price)

                group.setStyleSheet("""
                    QGroupBox {
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        margin: 10px;
                        padding: 15px;
                    }
                    QLabel {
                        font-size: 12px;
                    }
                """)
                title.setStyleSheet("font-weight: bold; font-size: 14px;")
                description.setStyleSheet("""
                    QLabel {
                        padding: 5px;
                        line-height: 1.4;
                        border: 1px solid #eee;
                        border-radius: 3px;
                        margin: 5px 0;
                    }
                """)
                price.setStyleSheet("font-weight: bold;")

                btn_rent = QPushButton("Управление бронированием")
                btn_edit_property = QPushButton("Изменить недвижимость")
                btn_remove_property = QPushButton("Удалить недвижимость")

                layout.addWidget(btn_rent)
                layout.addWidget(btn_remove_property)
                layout.addWidget(btn_edit_property)

                group.setLayout(layout)
                content_layout.addWidget(group)

                btn_rent.clicked.connect(
                    lambda checked, p=prop: self.rent_property(p)
                )
                btn_edit_property.clicked.connect(
                    lambda checked, p=prop: self.edit_property(p)
                )
                btn_remove_property.clicked.connect(
                    lambda checked, p=prop: self.remove_property(p)
                )

        scroll_area.setWidget(content)

        # Очищаем предыдущие результаты
        if self.property_list_layout.count() > 0:
            old_widget = self.property_list_layout.takeAt(0).widget()
            old_widget.deleteLater()
            
        self.property_list_layout.addWidget(scroll_area)

    def create_description_widget(self, text):
        container = QWidget()
        layout = QVBoxLayout(container)
        
        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignJustify)
        
        btn = QPushButton("Показать полностью")
        btn.setCheckable(True)
        label.setMaximumHeight(80)
        btn.clicked.connect(lambda: self.toggle_description(label, btn))
        
        layout.addWidget(label)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        return container

    def toggle_description(self, label, btn):
        if btn.isChecked():
            label.setMaximumHeight(16777215)
            btn.setText("Свернуть")
        else:
            label.setMaximumHeight(80)
            btn.setText("Показать полностью")

    def load_data_from_db(self):
        self.property_categories = self.db.get_property_categories()
        if not self.property_categories:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить категории")
            self.close()

        self.amenities = self.db.get_amenities()
        if not self.amenities:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список удобств")
            return
    
    def filter_search(self):
        search_text = self.property_searchbar.text().strip()
        selected_amenities = [name for name, cb in self.amenity_checkboxes.items() if cb.isChecked()]
        selected_categories = [name for name, cb in self.categories_checkboxes.items() if cb.isChecked()]
        selected_status = [name for name, cb in self.booking_status_checkboxes.items() if cb.isChecked()]
        
        has_active_booking = None
        if self.active_text in selected_status and self.inactive_text not in selected_status:
            has_active_booking = True
        elif self.inactive_text in selected_status and self.active_text not in selected_status:
            has_active_booking = False
        
        categories = selected_categories if selected_categories else None
        amenities = selected_amenities if selected_amenities else None
        
        properties = self.db.get_properties(
            search_query=search_text or None,
            categories=categories,
            amenities=amenities,
            has_active_booking=has_active_booking
        )
        self.scroll_list_property(properties if properties else [])

    def reset_filters(self):
        for cb in self.amenity_checkboxes.values():
            cb.setChecked(False)
        for cb in self.categories_checkboxes.values():
            cb.setChecked(False)
        for cb in self.booking_status_checkboxes.values():
            cb.setChecked(False)
        self.search_property()

    def search_property(self):
        try:
            search_text = self.property_searchbar.text().strip()
            properties = self.db.get_properties(search_text if search_text else None)
            if properties is None:
                QMessageBox.critical(self, "Ошибка", "Не удалось загрузить данные")
                return
            self.scroll_list_property(properties)
        except Exception as e:
            print(str(e))
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при выполнении поиска")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()