from log import log
from urllib.parse import parse_qs, urlparse

# 笔记内链 wiz://open_document/?guid=bda9f178-04d5-4cbb-a054-e691b81e87a0&kbguid=&private_kbguid=3d251a9b-2f9a-102d-bd16-dd2e4f011a7d
# 附件内链 wiz://open_attachment?guid=52a00459-92d8-4b9f-b2b7-d3fb6708559d


class WizInternalLink(object):
    """ 嵌入 html 正文中的为知笔记内部链接，可能是笔记，也可能是附件
    """

    guid: str = None
    """ 原始链接中的资源 guid，可能是 attachment 或者是 wiz_document
    """

    link_type: str = None
    """ 值为 open_attachment 或者 open_document
    """

    def __init__(self, wiz_internal_link: str) -> None:
        """解析 wiz 内部链接

        Args:
            wiz_internal_link (str): wiz内链，应当是 `wiz://` 开头
        """

        url = urlparse(wiz_internal_link)
        if (url.scheme != 'wiz'):
            log.error(f"wiz 内部链接必须以 `wiz://` 开头：`{wiz_internal_link}`")
            return

        self.guid = parse_qs(url.query)['guid'][0]
        self.link_type = url.hostname

    def is_attachment(self):
        return "open_attachment" == self.link_type

    def is_document(self):
        return "open_document" == self.link_type
