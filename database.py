import psycopg2
from typing import Optional, Dict, List

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.set_default_bg()

    def set_default_bg(self):
        self.config = {
            "user": "postgres",
            "password": "S123456s",
            "host": "127.0.0.1",
            "port": "5432",
            "database": "SmartBooking"
        }
        self.connect()

    def get_config(self):
        return self.config
    
    def set_config(self, user_bd, pass_bd, host_bd, port_bd, database):
        self.config = {
            "user": user_bd,
            "password": pass_bd,
            "host": host_bd,
            "port": port_bd,
            "database": database
        }
        return self.connect()
    
    def connect(self) -> bool:
        # Установка соединения с базой данных
        try:
            self.connection = psycopg2.connect(**self.config)
            return True
        except psycopg2.Error as e:
            print(f"Ошибка подключения: {e}")
            self.set_default_bg()
            return False
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False) -> Optional[List[Dict]]:
        # Универсальный метод для выполнения запросов
        try:
            with self.connection.cursor() as cursor:
                #print("Параметры:", params)
                cursor.execute(query, params)
                if fetch:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.connection.commit()
                return None
        except psycopg2.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            self.connection.rollback()
            return None
    
    def close(self):
        # Закрытие соединения
        if self.connection:
            self.connection.close()
    
    def get_property_categories(self) -> list:
        query = """
            SELECT enumlabel AS name 
            FROM pg_enum 
            WHERE enumtypid = 'property_category'::regtype
            ORDER BY enumsortorder
        """
        result = self.execute_query(query, fetch=True)
        return [row['name'] for row in result] if result else []
    
    def get_properties_by_type(self, property_type: str):
        query = "SELECT * FROM property WHERE property_type = %s::property_category"
        return self.execute_query(query, (property_type,), fetch=True)

    def get_properties_with_amenities(self):
        query = """
            SELECT 
                p.*,
                array_agg(a.name) AS amenities
            FROM property p
            LEFT JOIN property_amenity pa ON p.property_id = pa.property_id
            LEFT JOIN amenity a ON pa.amenity_id = a.amenity_id
            GROUP BY p.property_id
        """
        result = self.execute_query(query, fetch=True)
        return [dict(row) for row in result] if result else []

    def get_amenities(self) -> list:
        # Получение списка удобств
        query = "SELECT name FROM amenity ORDER BY name"
        result = self.execute_query(query, fetch=True)
        return [row['name'] for row in result] if result else []

    def get_properties(self, search_query=None, categories=None, amenities=None, has_active_booking=None):
        query = "SELECT * FROM get_filtered_properties(%s, %s, %s, %s)"
        return self.execute_query(
            query,
            (
                search_query,
                categories or [],
                amenities or [],
                has_active_booking
            ),
            fetch=True
        )