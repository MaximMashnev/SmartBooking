import re
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QMessageBox, QComboBox, QLabel, QVBoxLayout, QDialog, QDialogButtonBox,
    QPushButton, QGroupBox, QLineEdit, QFormLayout, QTableWidget, QDateEdit, QTableWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QIcon

class BookingManagementWindow(QWidget):
    windowClosed = pyqtSignal()
    
    def __init__(self, main_window=None, property_data=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowTitleHint)
        self.setMinimumSize(700, 500)
        self.main_window = main_window
        self.property_data = property_data
        self.status_list = ["активен", "отменен", "завершен"]
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Управление бронированием")
        self.setWindowIcon(QIcon(self.main_window.set_logo()))
        self.create_ui()

    def closeEvent(self, event):
        self.windowClosed.emit()
        self.main_window.setEnabled(True)
        event.accept()

    def create_ui(self):
        main_layout = QVBoxLayout()
        
        info_group = QGroupBox("Информация о недвижимости")
        info_layout = QVBoxLayout()
        title_property = QLabel(f"Название: {self.property_data['title']}")
        property_type = QLabel(f"Тип размещения: {self.property_data['property_type']}")
        info_layout.addWidget(title_property)
        info_layout.addWidget(property_type)
        info_group.setLayout(info_layout)
        
        self.bookings_table = QTableWidget()
        self.bookings_table.setColumnCount(6)
        self.bookings_table.setHorizontalHeaderLabels([
            "ID", "Email", "Начало", "Конец", "Статус", "Дата создания"
        ])
        self.bookings_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.bookings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.bookings_table.setSortingEnabled(True)
        self.bookings_table.horizontalHeader().setStretchLastSection(True)
        
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить бронь", clicked=self.add_booking)
        self.edit_btn = QPushButton("Изменить", clicked=self.edit_booking)
        self.delete_btn = QPushButton("Удалить", clicked=self.delete_booking)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        
        main_layout.addWidget(info_group)
        main_layout.addWidget(QLabel("Список бронирований:"))
        main_layout.addWidget(self.bookings_table)
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
        self.load_bookings()

    def load_bookings(self):
        try:
            query = """
                SELECT booking_id, user_email, start_date, end_date, status, created_at 
                FROM booking 
                WHERE property_id = %s
                ORDER BY start_date DESC
            """
            result = self.main_window.db.execute_query(
                query, 
                (self.property_data['property_id'],),
                fetch=True
            )
            
            if result is None:
                result = []
                
            self.bookings_table.setRowCount(len(result))
            
            for row_idx, row in enumerate(result):
                values = [
                    row['booking_id'],
                    row['user_email'],
                    row['start_date'].strftime("%d.%m.%Y"),
                    row['end_date'].strftime("%d.%m.%Y"),
                    row['status'],
                    row['created_at'].strftime("%d.%m.%Y %H:%M")
                ]
                for col_idx, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    self.bookings_table.setItem(row_idx, col_idx, item)
                    
        except Exception as e:
            print(str(e))
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки брони из базы данных")
            self.bookings_table.setRowCount(0)

    def add_booking(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Создание брони")
        dialog.setFixedHeight(150)
        
        form = QFormLayout()
        email_new = QLineEdit()
        email_new.setMaxLength(50)
        start_edit = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        end_edit = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        status_combo = QComboBox()
        status_combo.addItems(self.status_list)
        
        form.addRow("Email:", email_new)
        form.addRow("Дата начала:", start_edit)
        form.addRow("Дата окончания:", end_edit)
        form.addRow("Статус:", status_combo)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok| QDialogButtonBox.StandardButton.Cancel)

        ok_button = btn_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Создать")
        
        cancel_button = btn_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("Отмена")

        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        
        form.addRow(btn_box)
        dialog.setLayout(form)    

        if dialog.exec() == QDialog.DialogCode.Accepted:
            email = email_new.text().strip()
            if start_edit.date().toPyDate() >= end_edit.date().toPyDate():
                QMessageBox.warning(self, "Ошибка", "Выбранный период дат неверен")
                return
            elif not self.validate_email(email):
                QMessageBox.warning(self, "Ошибка", "Некорректный email")
                return
            else:
                query = """
                    INSERT INTO booking 
                    (property_id, user_email, start_date, end_date, status)
                    VALUES (%s, %s, %s, %s, %s)
                """
                try:
                    self.main_window.db.execute_query(query, (
                        self.property_data['property_id'],
                        email,
                        start_edit.date().toPyDate(),
                        end_edit.date().toPyDate(),
                        status_combo.currentText()
                    ))
                    QMessageBox.information(self, "Успех", "Бронь успешно добавлена!")
                    self.load_bookings()
                except Exception as e:
                    print(str(e))
                    QMessageBox.critical(self, "Ошибка", "Ошибка при добавлении брони")

    def edit_booking(self):
        selected = self.bookings_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите бронь для редактирования")
            return
        
        booking_id = self.bookings_table.item(selected, 0).text()
        
        query = "SELECT * FROM booking WHERE booking_id = %s"
        result = self.main_window.db.execute_query(query, (booking_id,), fetch=True)
        
        if not result:
            QMessageBox.critical(self, "Ошибка", "Данные не найдены")
            return
        data = result[0]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование брони")
        layout = QFormLayout()
        
        email_edit = QLineEdit(data['user_email'])
        start_edit = QDateEdit(data['start_date'])
        end_edit = QDateEdit(data['end_date'])
        status_combo = QComboBox()
        status_combo.addItems(self.status_list)
        status_combo.setCurrentText(data['status'])
        
        layout.addRow("Email:", email_edit)
        layout.addRow("Начало:", start_edit)
        layout.addRow("Конец:", end_edit)
        layout.addRow("Статус:", status_combo)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        ok_button = btn_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Сохранить")
        
        cancel_button = btn_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("Отмена")

        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addRow(btn_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            email = email_edit.text().strip()
            if not self.validate_email(email):
                QMessageBox.warning(self, "Ошибка", "Некорректный email")
                return
            else:
                update_query = """
                    UPDATE booking SET
                        user_email = %s,
                        start_date = %s,
                        end_date = %s,
                        status = %s
                    WHERE booking_id = %s
                """
                try:
                    self.main_window.db.execute_query(
                        update_query,
                        (
                            email,
                            start_edit.date().toPyDate(),
                            end_edit.date().toPyDate(),
                            status_combo.currentText(),
                            booking_id
                        )
                    )
                    QMessageBox.information(self, "Успех", "Бронь успешно изменена!")
                    self.load_bookings()
                except Exception as e:
                    print(str(e))
                    QMessageBox.critical(self, "Ошибка", "Ошибка при сохранении изменений")

    def delete_booking(self):
        selected = self.bookings_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите бронь для удаления")
            return
        
        msg_box = QMessageBox(
            QMessageBox.Icon.Question,
            "Подтверждение",
            "Удалить выбранную бронь?",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            parent=self
        )

        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        yes_button.setText("Да")

        no_button = msg_box.button(QMessageBox.StandardButton.No)
        no_button.setText("Нет")

        booking_id = self.bookings_table.item(selected, 0).text()
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            try:
                self.main_window.db.execute_query(
                    "DELETE FROM booking WHERE booking_id = %s",
                    (booking_id,)
                )
                self.load_bookings()
            except Exception as e:
                print(str(e))
                QMessageBox.critical(self, "Ошибка", "Ошибка при удалении брони")

    def save_booking(self):
        email = email.text().strip()
        if not self.validate_email(email):
            QMessageBox.warning(self, "Ошибка", "Некорректный email")
            return

        query = """
            INSERT INTO booking (property_id, user_email, start_date, end_date)
            VALUES (%s, %s, %s, %s)
        """
        try:
            self.main_window.db.execute_query(
                query,
                (
                    self.property_data['property_id'],
                    email,
                    self.start_date_edit.date().toPyDate(),
                    self.end_date_edit.date().toPyDate()
                )
            )
        except Exception as e:
            print(str(e))
            QMessageBox.critical(self, "Ошибка", "Ошибка при сохранении брони")

    def validate_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.fullmatch(pattern, email) is not None