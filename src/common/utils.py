import chardet
from pathlib import Path

def get_html_file_content(html_file: Path):
    """
    读取html文件为字符串文本

    支持自动检测文件编码
    """
    html_body_bytes = html_file.read_bytes()
    # 检测文件编码
    enc = chardet.detect(html_body_bytes)
    return html_body_bytes.decode(encoding=enc['encoding'] or 'utf-8')

def date_str2timestamp(date_str: str, format="%Y-%m-%d %H:%M:%S"):
    """ 将日期字符串转为时间 """
    from datetime import datetime
    return datetime.strptime(date_str, format).timestamp()
