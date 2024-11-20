from datetime import datetime
from pathlib import Path

from .wiz_attachment import WizAttachment
from .wiz_tag import WizTag

FORMAT_STRING = "%Y-%m-%d %H:%M:%S"


class WizDocument(object):
    """ 为知笔记文档
        DOCUMENT_GUID, DOCUMENT_TITLE, DOCUMENT_LOCATION, DOCUMENT_NAME,
        DOCUMENT_TYPE, DT_CREATED, DT_MODIFIED, DT_ACCESSED, DOCUMENT_ATTACHMENT_COUNT
    """
    # 文档的 guid
    guid: str = None
    title: str = None

    # 文件夹，为知笔记的文件夹就是一个用 / 分隔的字符串
    location: str = None
    name: str = None
    type: str = None

    created: str = None
    modified: str = None
    accessed: str = None

    # 从数据库中读取的附件数量，如果大于 0 说明这个文档有附件
    attachment_count: int = 0

    # 文档的标签
    tags: list[WizTag] = []

    # 文档的附件
    attachments: list[WizAttachment] = []

    file: Path = None
    attachments_dir: Path = None

    def __init__(self, guid: str, title: str, location: str, name: str, type: str, created: str, modified: str, accessed: str, attachment_count: int, wiz_dir: Path) -> None:
        self.guid = guid
        self.title = title
        self.location = location
        self.name = name
        self.type = type
        self.created = created
        self.modified = modified
        self.accessed = accessed
        self.attachment_count = attachment_count
        self.wiz_dir = wiz_dir

        self.file = Path(str(self.wiz_dir) + self.location + self.name).expanduser()

        if self.attachment_count == 0:
            return
        self.attachments_dir = Path(str(self.file.parent.joinpath(self.file.stem)) + "_Attachments")
        # if not self.attachments_dir.exists():
        #     raise FileNotFoundError(f'找不到附件文件夹 `{self.attachments_dir}`！')

    def resolve_attachments(self, attachments: list[WizAttachment]) -> None:
        self.attachments = attachments
        # if len(self.attachments) != self.attachment_count:
        #     raise ValueError(f'附件数量不匹配 {len(self.attachments)} != {self.attachment_count}！')

    def resolve_tags(self, tags: list[WizTag]) -> None:
        self.tags = tags

    def is_markdown(self):
        return self.title.endswith('.md')

    def is_todolist(self, file_extract_dir: Path):
        # 部分情况下 type 为 null，根据是否存在 wiz_todolist.xml 来判断，增加鲁棒性
        # 可以直接根据 wiz_todolist.xml 来判断，考虑存在未知的情况，暂时不动
        return self.type == "todolist2" or file_extract_dir.joinpath("index_files").joinpath("wiz_todolist.xml").exists()

    def get_created(self):
        return datetime.strptime(self.created, FORMAT_STRING).timestamp()

    def get_modified(self):
        return datetime.strptime(self.modified, FORMAT_STRING).timestamp()

    def get_accessed(self):
        return datetime.strptime(self.accessed, FORMAT_STRING).timestamp()

    def gen_front_matter(self):
        front_matter = ["---"]
        tags = self._gen_tags()
        if tags:
            front_matter.append(tags)
        front_matter.append(f"date: {self.created}")
        front_matter.append("---")
        return "\n".join(front_matter)

    def _gen_tags(self):
        if len(self.tags) == 0:
            return None

        tags = []
        for tag in self.tags:
            tags.append(f'  - {tag.name}')

        tags = "\n".join(tags)

        return f"tags:\n{tags}"
