import chardet
import html2text
from pathlib import Path


def html2md(html_file: Path):
    """
    把指定的html文件转换为 Markdown 格式的文本
    """
    html_content = html_file2str(html_file)
    return html2text.html2text(html_content)


def html_file2str(html_file: Path):
    """
    把指定的html文件读取为字符串文本
    """
    html_body_bytes = html_file.read_bytes()
    # 早期版本的 html 文件使用的是 UTF-16 LE(BOM) 编码保存。最新的文件是使用 UTF-8(BOM) 编码保存。要判断编码进行解析
    enc = chardet.detect(html_body_bytes)
    return html_body_bytes.decode(encoding=enc['encoding'])
