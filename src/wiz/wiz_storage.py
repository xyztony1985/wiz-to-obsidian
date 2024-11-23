from os import path
from pathlib import Path

from .wiz_db import DB
from .entity.wiz_tag import WizTag
from .entity.wiz_attachment import WizAttachment
from .entity.wiz_document import WizDocument
from convertor_db import ConvertorDB


class WizStorage(object):
    wiz_dir: Path
    wiz_db: DB
    convertor_db: ConvertorDB

    # 所有的文档
    documents: list[WizDocument] = []

    def __init__(self, wiz_dir: str):
        """ 从 `wiz_dir` 找到为知的数据库文件，读取所有笔记信息到本对象，方便后续操作。
        :param wiz_dir: 笔记文件夹路径
        """
        self.wiz_dir = Path(wiz_dir).expanduser()
        print(f'\n\n账号:{path.basename(wiz_dir)}')

        self.wiz_db = DB(self.wiz_dir)
        self.convertor_db = ConvertorDB()

        self._init()

    def _init(self):
        rows = self.wiz_db.get_all_document()
        for row in rows:
            document = WizDocument(*row, self.wiz_dir)
            self.documents.append(document)
            document.resolve_attachments(self._get_attachments(document.guid))
            document.resolve_tags(self._get_tags(document.guid))
            
            self.convertor_db.add(document)

    def _get_attachments(self, document_guid: str) -> list[WizAttachment]:
        rows = self.wiz_db.get_document_attachments(document_guid)
        attachments: list[WizAttachment] = []
        for row in rows:
            attachments.append(WizAttachment(*row))
        return attachments

    def _get_tags(self, document_guid: str) -> list[WizTag]:
        rows = self.wiz_db.get_document_tags(document_guid)
        tags: list[WizTag] = []
        for row in rows:
            tags.append(WizTag(*row))
        return tags

    def get_document(self, document_guid: str):
        row = self.wiz_db.get_document(document_guid)
        if not row:
            return None
        document = WizDocument(*row, self.wiz_dir)
        document.resolve_attachments(self._get_attachments(document.guid))
        document.resolve_tags(self._get_tags(document.guid))
        return document
