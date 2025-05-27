import psycopg2
import json
import psycopg2.extras

class UserRepository:
    def __init__(self, host, port, user, password, database):
        self.connection_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "dbname": database,
        }
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                **self.connection_params,
                #cursor_factory=psycopg2.extras.RealDictCursor
            )
            #print("Connected to PostgreSQL server with params: ", self.connection_params)
        except Exception as e:
            print("Connection failed:", e)

    def close(self):
        if self.conn:
            self.conn.close()
            print("Connection closed.")

    # def get_user_count(self):
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute("SELECT COUNT(*) FROM users;")
    #             result = cursor.fetchone()
    #             return result
    #     except Exception as e:
    #         print("Count failed:", e)
    #         return None
        
    # def get_user_list(self):
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute("SELECT * FROM users;")
    #             return cursor.fetchall()
    #     except Exception as e:
    #         print("List failed:", e)
    #         return None
        
    # def get_high_skill_users(self, skill: bool):
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute("SELECT * FROM users WHERE HighlySkilled = %s;", (skill,))
    #             return cursor.fetchall()
    #     except Exception as e:
    #         print("High skill users failed:", e)
    #         return None

    def get_items_by_brand(self, brand: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""SELECT p.product_name, p.description, p.price 
                                  FROM products p 
                                  inner join brands b on p.brand_id = b.brand_id 
                                  WHERE UPPER(b.brand_name) LIKE UPPER(%s);""", (brand,))
                return cursor.fetchall()
        except Exception as e:
            print("Get items by brand failed:", e)
            return None
    
    def get_items_by_category(self, category: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""SELECT p.product_name, p.description, p.price  
                                  FROM products p
                                  inner join categories c on p.category_id = c.category_id
                                  WHERE UPPER(c.category_name) = UPPER(%s);""", (category,))
                return cursor.fetchall()
        except Exception as e:
            print("Get items by category failed:", e)
            return None

    def get_items_by_brand_and_category(self, brand: str, category: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""SELECT p.product_name, p.description, p.price  
                                  FROM products p
                                  INNER JOIN brands b ON p.brand_id = b.brand_id
                                  INNER JOIN categories c ON p.category_id = c.category_id
                                  WHERE UPPER(b.brand_name) = UPPER(%s) AND UPPER(c.category_name) = UPPER(%s);""", (brand, category))
                return cursor.fetchall()
        except Exception as e:
            print("Get items by brand and category failed:", e)
            return None