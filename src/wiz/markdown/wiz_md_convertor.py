import os
from urllib.parse import urlparse

import requests
from pathlib import Path

from parser import html2md
from log import log

from .wiz_md_paser import parse_wiz_html
from ..entity.wiz_attachment import WizAttachment
from ..entity.wiz_image import WizImage
from ..wiz_storage import WizStorage


def convert_md(file_extract_dir: Path, attachments: list[WizAttachment], target_path: str, target_file: Path, target_attachments_dir: Path, wiz_storage: WizStorage):
    # 解析 index.html 文件正文中的图像文件，将其转换为 WizImage，将正文存入 body
    body, internal_links, images = parse_wiz_html(file_extract_dir)

    for internal_link in internal_links:
        # 附件
        if internal_link.is_open_attachment():
            attachment_link = _build_attachment_link(internal_link, attachments, target_attachments_dir)
            if not attachment_link:
                continue
            body = body.replace(internal_link.outer_html, attachment_link)
        # Link
        if internal_link.is_open_document():
            # return f"[{internal_link.title}](未命名.md)"
            # 找到 document，生成相对路径
            document = wiz_storage.get_document(internal_link.guid)
            if not document:
                print(f"{internal_link.title} {internal_link.guid} 文档找不到")
                continue
            # 找到 document 相对当前文件的相对路径
            path = os.path.relpath(str(document.location + document.title), os.path.dirname(str(target_path)))
            body = body.replace(internal_link.outer_html, f"[{document.title}]({path})")

    for image in images:
        if image.is_http():
            body = body.replace(image.outer_html, f'![]({image.src})')
            # image_file = _download_image(image, target_attachments_dir)
            # if image_file:
            #     # 图片下载成功使用下载后的文件
            #     body = body.replace(image.outer_html, f'![]({target_attachments_dir.name}/{image_file.name})')
            # else:
            #     # 使用 src
            #     body = body.replace(image.outer_html, f'![]({image.src})')
        else:
            _convert_image(image, file_extract_dir, target_attachments_dir)
            body = body.replace(image.outer_html, f'![]({target_attachments_dir.name}/{Path(image.src).name})')

    temp_file = target_file.parent.joinpath(target_file.stem + ".html")

    # 保存临时文件
    temp_file.write_text(body, "UTF-8")

    temp_path = "file://" + str(temp_file)
    # 转义 ?
    temp_path = temp_path.replace("?", "%3F")

    markdown = html2md(temp_file)

    if markdown == "":
        log.warning("Markdown is empty.")

    target_file.write_text(markdown, "UTF-8")

    temp_file.unlink()


def _build_attachment_link(internal_link, attachments, target_attachments_dir):
    attachment = _get_attachment(attachments, internal_link.guid)
    if not attachment:
        print(f"{internal_link.title} {internal_link.guid} 找不到附件")
        return
    return f'![]({target_attachments_dir.name}/{attachment})'


def _get_attachment(attachments: list[WizAttachment], guid: str):
    for attachment in attachments:
        if attachment.guid == guid:
            return attachment.name
    return None


def _convert_image(image: WizImage, file_extract_dir: Path, target_attachments_dir: Path):
    if not target_attachments_dir.exists():
        target_attachments_dir.mkdir(parents=True)
    image_file = Path(str(file_extract_dir) + "/" + image.src)
    if not image_file.exists():
        raise RuntimeError(f"{image_file} 文件不存在")
    target_image_file = Path(str(target_attachments_dir) + "/" + Path(image.src).name)
    target_image_file.write_bytes(image_file.read_bytes())
    os.utime(target_image_file, (os.path.getatime(image_file), os.path.getmtime(image_file)))


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
