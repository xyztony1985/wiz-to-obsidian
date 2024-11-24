from urllib.parse import urlparse
import requests
from pathlib import Path
from log import log
from ..entity.wiz_attachment import WizAttachment
from ..entity.wiz_image import WizImage
from ..wiz_storage import WizStorage
import re
import shutil
from bs4 import BeautifulSoup
from utils import get_html_file_content
from config import Config
from wiz.entity.wiz_internal_link import WizInternalLink
from markdownify import MarkdownConverter

def convert_md(file_extract_dir: Path, attachments: list[WizAttachment], target_path: str, target_file: Path, target_attachments_dir: Path, wiz_storage: WizStorage):
    markdown = wiz_html_to_md(file_extract_dir, attachments, target_attachments_dir, wiz_storage)
    markdown = markdown.replace("\r\n", "\n")  #避免多余的空行
    target_file.write_text(markdown, "UTF-8")
    if markdown == "":
        log.warning("Markdown is empty.")

def wiz_html_to_md(file_extract_dir: Path, attachments: list[WizAttachment], target_attachments_dir: Path, wiz_storage: WizStorage):

    if not isinstance(file_extract_dir, Path):
        file_extract_dir = Path(file_extract_dir)

    html_file = file_extract_dir.joinpath("index.html")
    if not html_file.exists():
        raise FileNotFoundError(f"主文档文件不存在！ {html_file}")

    # 用 BeautifulSoup 解析 wiz html
    html_content = get_html_file_content(html_file)
    soup = BeautifulSoup(html_content, "html.parser")

    # 计算图片或附件的相对路径，在处理内链时用到
    attachment_relative_path = str(target_attachments_dir.relative_to(Config.output_dir)).replace('\\','/') + '/'

    # 处理图片链接
    # <img src="index_files/1cde3ccd-3c93-413f-8582-fa727bc19afe.png"/>
    # index_files 替换为 target_attachments_dir基于ouptut_dir的相对路径
    # obsidian的内链图片格式为：![[filename]]
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and src.startswith("index_files/"):
            internal_link = src.replace("index_files/", attachment_relative_path)
            img.replace_with(f'![[{internal_link}]]')
            _convert_image(file_extract_dir.joinpath(src), target_attachments_dir)

    # 处理内链：直接转为 obsidian 的内链格式
    # 笔记内链 <a href="wiz://open_document/?guid=bda9f178-04d5-4cbb-a054-e691b81e87a0&kbguid=&private_kbguid=3d251a9b-2f9a-102d-bd16-dd2e4f011a7d">text</a>
    # 附件内链 <a href="wiz://open_attachment?guid=52a00459-92d8-4b9f-b2b7-d3fb6708559d">
    # obsidian 的内链格式为：[[Internal links|custom display text]]
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and href.startswith("wiz://"):
            link = WizInternalLink(href)
            # 笔记内链
            if link.is_document():
                # 找到 document，生成相对路径
                document = wiz_storage.get_document(link.guid)
                if not document:
                    log.warning(f"处理笔记内链：{link.guid} 文档找不到")
                    continue
                internal_link = document.location + document.output_file_name
                a.replace_with(f'[[{internal_link}|{a.text}]]')
            # 附件内链
            else:
                internal_link = attachment_relative_path + _get_attachment(attachments, link.guid)
                a.replace_with(f'[[{internal_link}]]')


    # 转换为 markdown
    return md(soup, 
              code_language_callback=callback,
              escape_asterisks=False,   #不转义 *
              escape_underscores=False, #不转义 _
              escape_misc=False,        #不转义其他符号
              heading_style='atx',       #atx格式：# 标题
              )


class CustomMarkdownConverter(MarkdownConverter):
    def convert_div(self, el, text, convert_as_inline):
        """ 默认没有处理div标签，这里按段落处理
        """
        return text+'\n\n'

def md(soup, **options):
    """
    Converting BeautifulSoup objects
    """
    return CustomMarkdownConverter(**options).convert_soup(soup)

def callback(pre):
    """
    为pre代码块返回语言名称
    """
    # <pre class="brush:python;toolbar:false">
    if pre.has_attr('class'):
        class_name = pre['class'][0]
        if 'brush:' in class_name:
            return re.search(r'brush:([^;]+)', class_name).group(1).strip()
        return class_name
    return None

def _get_attachment(attachments: list[WizAttachment], guid: str):
    for attachment in attachments:
        if attachment.guid == guid:
            return attachment.name
    return None

def _convert_image(img_file_path: Path, target_attachments_dir: Path):
    if not target_attachments_dir.exists():
        target_attachments_dir.mkdir(parents=True)
    shutil.copy2(img_file_path, target_attachments_dir)

def _download_image(image: WizImage, target_attachments_dir: Path):
    if not target_attachments_dir.exists():
        target_attachments_dir.mkdir(parents=True)
    try:
        response = requests.get(image.src, timeout=(1, 1))
        if response.status_code != 200:
            # raise RuntimeError(f"{image.src} 下载失败")
            print(f"{image.src} 下载失败")
            return None
    except Exception:
        print(f"{image.src} 下载失败")
        return None
    # except Exception as e:
        # raise e

    file_name = Path(urlparse(image.src).path).stem

    content_type = response.headers["Content-Type"]
    if "image/jpeg" in content_type:
        file_name += ".jpg"
    elif "image/png" in content_type:
        file_name += ".png"
    elif "image/gif" in content_type:
        file_name += ".gif"

    image_file = target_attachments_dir.joinpath(file_name)

    image_file.write_bytes(response.content)

    return image_file
