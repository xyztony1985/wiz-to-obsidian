from pathlib import Path
from log import log
from ..entity.wiz_attachment import WizAttachment
from ..wiz_storage import WizStorage
import re
import shutil
from bs4 import BeautifulSoup, NavigableString
from utils import get_html_file_content
from config import Config
from wiz.entity.wiz_internal_link import WizInternalLink
from markdownify import MarkdownConverter

def wiz_html_to_md(index_html_file: Path, attachments: list[WizAttachment], target_attachments_dir: Path, wiz_storage: WizStorage):
    # 用 BeautifulSoup 解析 wiz html
    html_content = get_html_file_content(index_html_file)
    soup = BeautifulSoup(html_content, "html.parser",
        multi_valued_attributes=None,    #不做多值属性解析，比如class属性值，默认解析为list，现在会合并为一个str
    )

    # 处理嵌套列表：转换不规范的嵌套列表html，这样后续 markdown 转换为 html 时，不会丢失嵌套列表
    # 见：[Nested List Formatting Issue](https://github.com/matthewwithanm/python-markdownify/issues/84)
    for list in soup.find_all(['ul','dl']):
        # 找上个兄弟节点，如果是空白文字节点，就继续往上找
        sibling = list.previous_sibling
        while sibling and isinstance(sibling, NavigableString) and sibling.strip() == '':
            sibling = sibling.previous_sibling
        # 上个兄弟节点是li，将当前的 ul 或 dl 节点移动到 li 节点的内部
        if sibling and sibling.name == 'li':
            sibling.append(list)

    # 计算图片或附件的相对路径，在处理内链时用到
    attachment_relative_path = str(target_attachments_dir.relative_to(Config.output_dir)).replace('\\','/') + '/'

    # 处理图片链接
    # <img src="index_files/1cde3ccd-3c93-413f-8582-fa727bc19afe.png"/>
    # index_files 替换为 target_attachments_dir基于ouptut_dir的相对路径
    # obsidian的内链图片格式为：![[filename]]
    for img in soup.find_all("img", src=lambda x: x and x.startswith("index_files/")):
        src = img.get("src")
        internal_link = src.replace("index_files/", attachment_relative_path)
        img.replace_with(f'![[{internal_link}]]')
        _convert_image(index_html_file.parent.joinpath(src), target_attachments_dir)

    # 处理内链：直接转为 obsidian 的内链格式
    # 笔记内链 <a href="wiz://open_document/?guid=bda9f178-04d5-4cbb-a054-e691b81e87a0&kbguid=&private_kbguid=3d251a9b-2f9a-102d-bd16-dd2e4f011a7d">text</a>
    # 附件内链 <a href="wiz://open_attachment?guid=52a00459-92d8-4b9f-b2b7-d3fb6708559d">
    # obsidian 的内链格式为：[[Internal links|custom display text]]
    for a in soup.find_all("a", href=lambda x: x and x.startswith("wiz://")):
        href = a.get("href")
        link = WizInternalLink(href)
        # 笔记内链
        if link.is_document():
            # 找到 document，生成相对路径
            document = wiz_storage.get_document(link.guid)
            if not document:
                log.warning(f"处理笔记内链：{link.guid} 文档找不到")
                continue
            internal_link = document.location + document.output_file_name
            a.replace_with(f'[[{internal_link}|{a.text.replace('\r','').replace('\n','')}]]')
        # 附件内链
        else:
            attachment_file_name = _get_attachment(link.guid, attachments)
            if attachment_file_name is None:
                log.warning(f"处理附件内链：{link.guid} 附件找不到")
                continue
            internal_link = attachment_relative_path + attachment_file_name
            a.replace_with(f'[[{internal_link}]]')


    # 转换为 markdown
    return md(soup, 
              code_language_callback=callback,
              escape_asterisks=False,   #不转义 *
              escape_underscores=False, #不转义 _
              escape_misc=False,        #不转义其他符号
              heading_style='atx',      #atx格式：# 标题
              )


class CustomMarkdownConverter(MarkdownConverter):
    def convert_div(self, el, text, convert_as_inline):
        """ 默认没有处理div标签，这里按段落处理
        """
        return text+'\n\n'

def md(soup, **options):
    """ Converting BeautifulSoup objects
    """
    return CustomMarkdownConverter(**options).convert_soup(soup)

def callback(pre):
    """ 为pre代码块返回语言名称
    """
    # <pre class="brush:python;toolbar:false">
    if pre.has_attr('class'):
        class_name = pre['class']
        code_lang = re.search(r'brush:([^;,]+)', class_name).group(1).strip() if 'brush:' in class_name else class_name
        return _fix_code_lang(code_lang)
    return None

def _fix_code_lang(lang):
    """
    Obsidian 使用 Prism 进行语法高亮
    
    如果在wiz使用了其他的语法高亮，少部分代码名称存在差异，需要在这里转换

    key: wiz中代码块的class名称
    value: Prism中代码块的class名称
    """
    code_dict = {
        "bat": "batch",
        "c#": "csharp",
        "cmd": "batch",
        "dos": "batch",
        "language-bash": "bash",
        "language-markup": "markup",
        "ps": "powershell",
    }
    return code_dict.get(lang) or lang

def _get_attachment(guid: str, attachments: list[WizAttachment]):
    """ 查找笔记中的附件的文件名 """
    for attachment in attachments:
        if attachment.guid == guid:
            return attachment.name
    return None

def _convert_image(img_file_path: Path, target_attachments_dir: Path):
    """ 将图片复制到目标目录 """
    if not target_attachments_dir.exists():
        target_attachments_dir.mkdir(parents=True)
    shutil.copy2(img_file_path, target_attachments_dir)
