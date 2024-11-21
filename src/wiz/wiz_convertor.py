import os
import sqlite3
import traceback
from log import log
from pathlib import Path
from zipfile import ZipFile, BadZipFile

from .entity.wiz_document import WizDocument
from .markdown.wiz_md_convertor import convert_md
from .todolist.wiz_td_convertor import convert_td
from .wiz_storage import WizStorage


def _convert_attachments(document: WizDocument, target_attachments_dir: Path):
    if len(document.attachments) == 0:
        return
    if not target_attachments_dir.exists():
        target_attachments_dir.mkdir(parents=True)
    for attachment in document.attachments:
        attachment_file = Path(str(document.attachments_dir) + "/" + attachment.name)
        target_attachment_file = Path(str(target_attachments_dir) + "/" + attachment.name)
        if not attachment_file.exists():
            print(f"{attachment_file} 附件未找到")
            continue
        target_attachment_file.write_bytes(attachment_file.read_bytes())
        os.utime(target_attachment_file, (os.path.getctime(attachment_file), os.path.getmtime(attachment_file)))


def _add_front_matter_and_update_time(file: Path, document: WizDocument):
    # 添加 front matter
    # tags 标签
    # date 创建时间
    text = file.read_text("UTF-8")
    text = document.gen_front_matter() + "\n" + text
    file.write_text(text, "UTF-8")
    # 更新修改时间及访问时间
    os.utime(file, (document.get_accessed(), document.get_modified()))


class WizConvertor(object):
    wiz_storage: WizStorage = None
    wiz_dir: str = None
    temp_dir: Path = None
    target_dir: Path = None

    # 转换过程中的专用数据库连接
    conn: sqlite3.Connection

    # lzf_db 的内容写入 json 文件中，避免每次都要重新生成 Folder，造成重复
    db_file: Path = None

    CREATE_SQL: str = """
        CREATE TABLE WIZ_CONVERTOR (
            GUID TEXT,
            LOCATION TEXT NOT NULL,
            NAME TEXT NOT NULL,
            TITLE TEXT NOT NULL,
            SUCCESS TEXT NOT NULL,
            PRIMARY KEY (guid)
        );
    """

    def __init__(self, wiz_dir: str):
        self.wiz_storage = WizStorage(wiz_dir)
        self.target_dir = Path(wiz_dir + "_w2o").expanduser()
        self.temp_dir = Path(wiz_dir + "_temp").expanduser()
        if not self.target_dir.exists():
            self.target_dir.mkdir()
        if not self.temp_dir.exists():
            self.temp_dir.mkdir()
        self._init_db()

    def _init_db(self):
        self.db_file = self.target_dir.joinpath("convertor.db")

        self.conn = sqlite3.connect(self.db_file)

        test_sql = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?;"

        table_exists = self.conn.execute(test_sql, ('WIZ_CONVERTOR',)).fetchone()[0]
        if not table_exists:
            self.conn.executescript(self.CREATE_SQL)

    def _is_converted(self, document_guid: str):
        """ 判断笔记是否已经转换
        """
        cur = self.conn.cursor()
        cur.execute(
            '''
            SELECT
                *
            FROM WIZ_CONVERTOR
            WHERE GUID = ?
            ''',
            (document_guid,)
        )
        row = cur.fetchone()
        if row:
            return True
        else:
            return False

    def _save_result(self, document: WizDocument, success: bool):
        self.conn.execute(
            """
            INSERT INTO
            WIZ_CONVERTOR(GUID, LOCATION, NAME, TITLE, SUCCESS)
            VALUES (?, ?, ?, ?, ?)
            """,
            (document.guid, document.location, document.name, document.title, success)
        )
        self.conn.commit()

    def convert(self):
        index = 0
        for document in self.wiz_storage.documents:
            index += 1
            try:
                self._convert_document(document, index, len(self.wiz_storage.documents))
            except Exception:
                print(f"处理失败 {traceback.format_exc()}")

    def _convert_document(self, document: WizDocument, index: int, total: int):
        print('')
        print(f"({index}/{total}) {document.location}{document.title}")

        # is_converted = self._is_converted(document.guid)
        # if is_converted:
        #     print('已处理过，跳过.')
        #     return

        # 转换前，做一些必要的检查
        if not document.file.exists():
            log.warning(f'找不到文件 `{document.file}`，可能没有下载，请检查！')
            return
        
        # 笔记名含有特殊字符的，需要替换掉
        invalid_chars  = '*"\\/<>:|?'  #obsidian的笔记的文件名不允许含有这些字符
        if any(char in document.title for char in invalid_chars):
            document.raw_title = document.title
            document.title = ''.join(['-' if char in invalid_chars else char for char in document.title])
            log.warning(f"文件名含有特殊字符，已做处理 `{document.raw_title}` -> `{document.title}`")            

        # 解压文档压缩包
        file_extract_dir = self._extract_zip(document)

        log.debug(f"{file_extract_dir}")

        target_file = Path(str(self.target_dir) + document.location + document.title).expanduser()
        if not target_file.parent.exists():
            target_file.parent.mkdir(parents=True)

        target_attachments_dir = Path(str(target_file) + "_Attachments")
        _convert_attachments(document, target_attachments_dir)

        if document.is_todolist(file_extract_dir):
            # todolist 转为 md
            target_file = Path(str(target_file) + ".md")
            convert_td(file_extract_dir, target_file)
            _add_front_matter_and_update_time(target_file, document)
            self._save_result(document, True)
            print(f"处理完成")
            return

        if not document.is_markdown():
            # 非 md 转为 md
            target_file = Path(str(target_file) + ".md")

        convert_md(file_extract_dir, document.attachments, document.location + document.title, target_file, target_attachments_dir, self.wiz_storage)
        _add_front_matter_and_update_time(target_file, document)
        self._save_result(document, True)
        print(f"处理完成. {'' if document.is_markdown() else '原笔记非Markdown格式，需手工检测正确性.'}")
        return

    def _extract_zip(self, document: WizDocument) -> Path:
        """ 解压缩当前文档的 zip 文件到 work_dir，以 guid 为子文件夹名称
        """
        file_extract_dir = self.temp_dir.joinpath(document.guid)
        # 如果目标文件夹已经存在，就不解压了
        if file_extract_dir.exists():
            return file_extract_dir

        try:
            zip_file = ZipFile(document.file)
            zip_file.extractall(file_extract_dir)
            return file_extract_dir
        except BadZipFile:
            log.error('解压失败，该笔记可能是加密笔记，请先解密')
