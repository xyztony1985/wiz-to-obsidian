from pathlib import Path
import chardet
import re

from wiz.entity.wiz_image import WizImage
from wiz.entity.wiz_internal_link import WizInternalLink

RE_A_START = r'<a href="'
RE_A_END = r'"[^>]*?>(.*?)</a>'

# 附件内链
# 早期的链接没有双斜杠
# wiz:open_attachment?guid=8337764c-f89d-4267-bdf2-2e26ff156098
# 后期的链接有双斜杠
# wiz://open_attachment?guid=52935f17-c1bb-45b7-b443-b7ba1b6f854e
RE_OPEN_ATTACHMENT_HREF = r'wiz:/{0,2}(open_\w+)\?guid=([a-z0-9\-]{36})'
RE_OPEN_ATTACHMENT_OUTER_HTML = RE_A_START + RE_OPEN_ATTACHMENT_HREF + RE_A_END

# 文档内链，只需要提取 guid 后面的部分即可
# wiz://open_document?guid=c6204f26-f966-4626-ad41-1b5fbdb6829e&amp;kbguid=&amp;private_kbguid=69899a48-dc52-11e0-892c-00237def97cc
RE_OPEN_DOCUMENT_HREF = r'wiz:/{0,2}(open_\w+)\?guid=([a-z0-9\-]{36})&amp;kbguid=&amp;private_kbguid=([a-z0-9\-]{36})'
RE_OPEN_DOCUMENT_OUTER_HTML = RE_A_START + RE_OPEN_DOCUMENT_HREF + RE_A_END

# 图像文件在 body 中存在的形式，即使是在 .md 文件中，也依然使用这种形式存在
# <img src="index_files/t_1042089910.jpg">
# <img src="http://img4.tbcdn.cn/L1/461/1/t_1042089910.jpg">
RE_IMAGE_OUTER_HTML = r'<img .*?src="((index_files/[^"]+)|(http[^"]+))"[^>]*?>'


def parse_wiz_html(file_extract_dir: Path) -> tuple[str, list[WizInternalLink], list[WizImage]]:
    """ 在为知笔记文档的 index.html 中搜索内链的附件和文档链接
    """
    index_html = file_extract_dir.joinpath('index.html')
    if not index_html.exists():
        raise FileNotFoundError(f'主文档文件不存在！ {index_html}')
    html_body_bytes = index_html.read_bytes()
    # 早期版本的 html 文件使用的是 UTF-16 LE(BOM) 编码保存。最新的文件是使用 UTF-8(BOM) 编码保存。要判断编码进行解析
    enc = chardet.detect(html_body_bytes)
    html_body = html_body_bytes.decode(encoding=enc['encoding'])

    # 去掉换行符，早期版本的 html 文件使用了 \r\n 换行符，而且会切断 html 标记。替换掉换行符方便正则
    html_body = html_body.replace('\r\n', '')
    html_body = html_body.replace('\n', '')

    internal_links: list[WizInternalLink] = []

    open_attachments = re.finditer(RE_OPEN_ATTACHMENT_OUTER_HTML, html_body, re.IGNORECASE)
    for open_attachment in open_attachments:
        outer_html = open_attachment.group(0).replace(open_attachment.group(3), "")
        # 附件展示为图片（<a><img></a>）时，忽略附件图片
        # 删除<a>...</>中的内容，避免 <a><img></a> 嵌套的 img 会被重复识别
        html_body = html_body.replace(open_attachment.group(0), outer_html)
        link = WizInternalLink(
            outer_html,
            open_attachment.group(2),
            "",
            open_attachment.group(1))
        internal_links.append(link)

    open_documents = re.finditer(RE_OPEN_DOCUMENT_OUTER_HTML, html_body, re.IGNORECASE)
    for open_document in open_documents:
        link = WizInternalLink(
            open_document.group(0),
            open_document.group(2),
            open_document.group(4),
            open_document.group(1))
        internal_links.append(link)

    images: list[WizImage] = []
    image_match = re.finditer(RE_IMAGE_OUTER_HTML, html_body, re.IGNORECASE)
    for image in image_match:
        img = WizImage(image.group(0), image.group(1))
        images.append(img)
    return html_body, internal_links, images
