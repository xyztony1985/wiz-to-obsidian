import sqlite3
from pathlib import Path


class DB(object):
    def __init__(self, wiz_dir: Path):
        self.wiz_dir = wiz_dir

        self.index_db = self.wiz_dir.joinpath('index.db')
        if not self.index_db.exists():
            raise FileNotFoundError(f'找不到数据库 {self.index_db.resolve()}！')

    def get_document(self, document_guid: str):
        """ 获取所有文档信息
        """
        conn = sqlite3.connect(self.index_db)
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT
                DOCUMENT_GUID, DOCUMENT_TITLE, DOCUMENT_LOCATION, DOCUMENT_NAME,
                DOCUMENT_TYPE, DT_CREATED, DT_MODIFIED, DT_ACCESSED, DOCUMENT_URL,
                DOCUMENT_ATTACHEMENT_COUNT as DOCUMENT_ATTACHMENT_COUNT
            FROM WIZ_DOCUMENT
            WHERE DOCUMENT_GUID = ?
            ''',
            (document_guid,)
        )
        row = cur.fetchone()
        conn.close()
        return row

    def get_all_document(self):
        """ 获取所有文档信息
        """
        conn = sqlite3.connect(self.index_db)
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT
                DOCUMENT_GUID, DOCUMENT_TITLE, DOCUMENT_LOCATION, DOCUMENT_NAME,
                DOCUMENT_TYPE, DT_CREATED, DT_MODIFIED, DT_ACCESSED, DOCUMENT_URL,
                DOCUMENT_ATTACHEMENT_COUNT as DOCUMENT_ATTACHMENT_COUNT
            FROM WIZ_DOCUMENT
            '''
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_document_attachments(self, document_guid: str) -> list:
        """ 获取某个文档的附件信息
        """
        conn = sqlite3.connect(self.index_db)
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT ATTACHMENT_GUID, DOCUMENT_GUID, ATTACHMENT_NAME, DT_DATA_MODIFIED
            FROM WIZ_DOCUMENT_ATTACHMENT
            WHERE DOCUMENT_GUID = ?
            ''',
            (document_guid,)
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_document_tags(self, document_guid: str) -> list:
        """ 获取某个文档的Tag信息
        """
        conn = sqlite3.connect(self.index_db)
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT DOCUMENT_GUID, WIZ_DOCUMENT_TAG.TAG_GUID, TAG_NAME
            FROM WIZ_DOCUMENT_TAG
            LEFT JOIN WIZ_TAG ON WIZ_DOCUMENT_TAG.TAG_GUID = WIZ_TAG.TAG_GUID
            WHERE DOCUMENT_GUID = ?
            ''',
            (document_guid,)
        )
        rows = cur.fetchall()
        conn.close()
        return rows
