import sqlite3
from common.log import log

class SQLiteBase:

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.connect()

    def connect(self):
        """连接到数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            log.debug(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            log.error(f"Failed to connect to database: {e}")

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            log.debug(f"Database connection closed at {self.db_path}")

    def execute(self, query, parameters=()):
        """执行SQL语句"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, parameters)
            self.conn.commit()
        except sqlite3.Error as e:
            log.error(f"Error executing query: {query}, parameters: {parameters}, error: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def query_list(self, query, parameters=()):
        """查询并返回结果列表"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, parameters)
            return cursor.fetchall()
        except sqlite3.Error as e:
            log.error(f"Error querying database: {query}, parameters: {parameters}, error: {e}")
            raise e
        finally:
            cursor.close()

    def query_one(self, query, parameters=()):
        """查询并返回一行结果"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, parameters)
            return cursor.fetchone()
        except sqlite3.Error as e:
            log.error(f"Error querying database: {query}, parameters: {parameters}, error: {e}")
            raise e
        finally:
            cursor.close()

    def query_scalar(self, query, parameters=()):
        """查询并返回首行首列的结果"""
        result = self.query_one(query, parameters)
        return result[0] if result else None
        