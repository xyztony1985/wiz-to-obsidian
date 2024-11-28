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
    """ 笔记名 """

    output_file_name: str = None
    """ 输出文件名，title值替换掉一些特殊字符 """

    location: str = None
    """ 笔记所属文件夹，格式为：`/folder1/folder2/.../` """
    name: str = None
    """ 笔记的文件名，格式为：`name.ziw`，ziw实际是zip压缩包 """
    type: str = None

    created: str = None
    modified: str = None
    accessed: str = None

    # 文档的标签
    tags: list[WizTag] = []

    # 从数据库中读取的附件数量，如果大于 0 说明这个文档有附件
    attachment_count: int = 0
    # 文档的附件
    attachments: list[WizAttachment] = []

    file: Path = None
    """ 笔记ziw文件的完整路径 """
    attachments_dir: Path = None

    # 笔记是从其他地方剪辑来的，一般会有来源网址
    url: str = None

    def __init__(self, guid: str, title: str, location: str, name: str, type: str, created: str, modified: str, accessed: str, url: str, attachment_count: int, wiz_dir: Path) -> None:
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
        self.url = url

        self.file = Path(str(self.wiz_dir) + self.location + self.name).expanduser()
        self._ensure_file_name_valid()

        if self.attachment_count == 0:
            return
        self.attachments_dir = Path(str(self.file.parent.joinpath(self.file.stem)) + "_Attachments")

    def resolve_attachments(self, attachments: list[WizAttachment]) -> None:
        self.attachments = attachments

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

    def _ensure_file_name_valid(self):
        """ 笔记名将做为文件名，不能含有某些特殊字符，需要替换掉，确保文件名合法

        `document.output_file_name`为最终文件名，是在`document.title`的基础上替换掉特殊字符
        """
        # key为文件名不允许出现的字符，value为替换为的字符
        char_to_replace = {
            "*": "-",
            '"': "''",
            "\\": "╲",
            "/": "╱",
            "<": "〈",
            ">": "〉",
            ":": "：",
            "|": "｜",
            "?": "？",
        }

        name = self.title
        for k in char_to_replace:
            name = name.replace(k, char_to_replace[k])

        # 文件名不能以.开头
        if (name.startswith('.')):
            name = '_' + name.strip('.')
        
        # 移除文件名中的.md
        # 为知的markdown笔记，文件名以`.md`结尾，这里要去掉，否则最终的输出文件名会有两个.md
        if (name.endswith('.md')):
            name = name.rstrip('.md')
        
        self.output_file_name = name
