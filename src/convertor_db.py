from common.log import log
from pathlib import Path

from common.sqlite_base import SQLiteBase
from common.utils import date_str2timestamp
from wiz.entity.wiz_document import WizDocument
from config import Config


class ConvertorDB(SQLiteBase):

    def __init__(self):
        """ 转换过程中的专用数据库
        """
        log.debug("init convertor db.")

        db = Path(Config.convertor_db_path)
        if not db.exists():
            db.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(str(db))

        table_exists = self.query_scalar("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='wiz_convertor';")
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
            extract_time TIMESTAMP, -- 提取笔记文件的时间
            PRIMARY KEY (guid)
        );
    """
            )

    def is_converted(self, document: WizDocument):
        """ 判断笔记是否已经转换
        """
        row = self.query_scalar(
            """
            SELECT count(*)
            FROM WIZ_CONVERTOR
            WHERE GUID = ? AND success=1
            """,
            (document.guid,),
        )
        # 转换后，笔记有更新，视为未转换
        return row and (not self.is_modified_after_extract(document))

    def save_result(self, document_guid: str, success: bool):
        self.execute(
            """
            UPDATE wiz_convertor SET
                success=?
            WHERE guid=?
            """,
            (success, document_guid)
        )

    def add(self, document: WizDocument):
        self.execute(
            """
            INSERT INTO wiz_convertor(guid, location, name, title, file_name)
            SELECT ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM wiz_convertor WHERE guid = ?)
            """,
            (document.guid, document.location, document.name, document.title, document.output_file_name or document.title, document.guid),
        )

    def save_extract_time(self, document_guid: str):
        """ 记录解压笔记的时间
        """
        self.execute(
            """
            UPDATE wiz_convertor SET
                extract_time = datetime('now', 'localtime')                
            WHERE guid=?
            """,
            (document_guid,)
        )

    def is_modified_after_extract(self, document: WizDocument):
        """ 解压后，笔记是否有更新
        """
        extract_time = self.query_scalar(
            """
            SELECT
                extract_time
            FROM WIZ_CONVERTOR
            WHERE GUID = ?
            """,
            (document.guid,)
        )
        
        return (not extract_time) or date_str2timestamp(extract_time) < document.get_modified()
