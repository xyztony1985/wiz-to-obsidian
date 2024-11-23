import traceback
from log import log
import sqlite3
from pathlib import Path

from wiz.entity.wiz_document import WizDocument
from config import Config


class ConvertorDB:

    def execute(self, query, parameters:tuple=()):
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, parameters)
            self.conn.commit()
        except Exception as e:
            log.error(f"execute error occurred: {traceback.format_exc()}")
            self.conn.rollback()
        finally:
            cursor.close()

    def query(self, query):
        cursor = self.conn.cursor()
        results = None
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            # 获取列名
            columns = [col[0] for col in cursor.description]

            # 转换为字典列表
            dict_list = [dict(zip(columns, row)) for row in results]
            return dict_list
        except Exception as e:
            log.exception(f"query error occurred: ")
            raise e
        finally:
            cursor.close()

    def __init__(self):
        """
        转换过程中的专用数据库
        """
        log.info("init db")

        db = Path(Config.convertor_db_path)
        if not db.exists():
            db.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db)

        table_exists = self.conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='wiz_convertor';").fetchone()[0]
        if not table_exists:
            self.execute(
                """
        CREATE TABLE wiz_convertor (
            guid TEXT,  -- wiz笔记的guid
            location TEXT NOT NULL, -- 笔记的相对路径
            name TEXT NOT NULL, -- 笔记的文件名
            title TEXT NOT NULL,    -- 笔记的标题
            file_name TEXT,      -- 转换后的文件名
            success INTEGER,
            PRIMARY KEY (guid)
        );
    """
            )

    def _is_converted(self, document_guid: str):
        """判断笔记是否已经转换"""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                *
            FROM WIZ_CONVERTOR
            WHERE GUID = ? AND success=1
            """,
            (document_guid,),
        )
        row = cur.fetchone()
        return True if row else False

    def save_result(self, document_guid: str, success: bool):
        self.conn.execute(
            """
            UPDATE wiz_convertor SET
                success=?
            WHERE guid=?
            """,
            (success, document_guid)
        )
        self.conn.commit()

    def add(self, document: WizDocument):
        self.execute(
            """
            INSERT INTO wiz_convertor(guid, location, name, title, file_name)
            SELECT ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM wiz_convertor WHERE guid = ?)
            """,
            (document.guid, document.location, document.name, document.title, document.output_file_name or document.title, document.guid),
        )
