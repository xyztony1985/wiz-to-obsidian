from pathlib import Path

from .wiz_db import WizDB
from .entity.wiz_tag import WizTag
from .entity.wiz_attachment import WizAttachment
from .entity.wiz_document import WizDocument
from convertor_db import ConvertorDB


class WizStorage(object):
    wiz_dir: Path
    wiz_db: WizDB
    convertor_db: ConvertorDB

    documents: list[WizDocument] = []
    """ 全部笔记文档 """

    all_tags: list[WizTag] = []
    """ 全部标签 """

    def __init__(self, wiz_dir: Path, wiz_db: WizDB, convertor_db: ConvertorDB):
        """ 从为知数据库，获取笔记、标签、附件等信息，并做一些必要处理，保存到本对象，方便后续操作。

        :param wiz_dir: 笔记文件夹路径
        """
        self.wiz_dir = wiz_dir
        self.wiz_db = wiz_db
        self.convertor_db = convertor_db

        self._init()

    def _init(self):
        # 获取所有标签，计算嵌套标签名
        self.all_tags = [WizTag(*tag) for tag in self.wiz_db.get_all_tag()]
        WizTag.compute_nesting_name(self.all_tags)

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
            tags.append(WizTag(*row).set_nesting_name(self.all_tags))
        return tags

    def get_document(self, document_guid: str):
        row = self.wiz_db.get_document(document_guid)
        if not row:
            return None
        document = WizDocument(*row, self.wiz_dir)
        document.resolve_attachments(self._get_attachments(document.guid))
        document.resolve_tags(self._get_tags(document.guid))
        return document
