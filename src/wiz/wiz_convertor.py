import os
import shutil
from common.log import log
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from config import Config
from convertor_db import ConvertorDB
from .entity.wiz_document import WizDocument
from .markdown.wiz_md_convertor import wiz_html_to_md
from .todolist.wiz_td_convertor import convert_td
from .wiz_storage import WizStorage


def _convert_attachments(document: WizDocument, target_attachments_dir: Path):
    """
    笔记如有附件，附件释放到 `target_attachments_dir`

    Args:
        target_attachments_dir (Path): 附件要释放到的目录
    """
    if len(document.attachments) != document.attachment_count:
        log.warning(f'附件数量不匹配，应有附件数：{document.attachment_count}，实有附件数：{len(document.attachments)}！')

    if len(document.attachments) == 0:
        log.debug("没有附件")
        return
    if not target_attachments_dir.exists():
        target_attachments_dir.mkdir(parents=True)
    for attachment in document.attachments:
        attachment_file = document.attachments_dir.joinpath(attachment.name)
        if not attachment_file.exists():
            log.warning(f"{attachment_file} 附件未找到")
            continue
        # copy2 拷贝文件，且保留文件属性
        shutil.copy2(attachment_file, target_attachments_dir)


def _add_front_matter_and_update_time(file: Path, document: WizDocument):
    """ 添加 front matter
    """
    front_matter = ["---"]

    # wiz document guid
    front_matter.append(f"wiz-guid: {document.guid}")

    # tags 标签
    if len(document.tags)>0:
        tags = "\n".join([f'  - {tag.nesting_name}' for tag in document.tags])
        front_matter.append(f"tags:\n{tags}")
        
    # date 创建时间
    front_matter.append(f"cdate: {document.created}")

    # aliases 标题别名： 原始笔记名修改过，则添加
    if document.title != document.output_file_name:
        front_matter.append(f'aliases: \n  - {document.title}')

    # 剪辑来源网址
    if document.url:
        front_matter.append(f"source: {document.url}")

    front_matter.append("---")

    text = file.read_text("UTF-8")
    text =  "\n".join(front_matter) + "\n" + text
    file.write_text(text, "UTF-8")

    # 更新修改时间及访问时间
    os.utime(file, (document.get_accessed(), document.get_modified()))


class WizConvertor(object):
    wiz_storage: WizStorage
    convertor_db: ConvertorDB
    temp_dir = Path(Config.temp_dir)
    target_dir = Path(Config.output_dir)
    """ 转换后笔记的相关文件，输出在这个目录下 """

    def __init__(self, convertor_db: ConvertorDB, wiz_storage: WizStorage):
        """ 为知笔记转换器，重点是html转为md
        """
        self.convertor_db = convertor_db
        self.wiz_storage = wiz_storage
        if not self.target_dir.exists():
            self.target_dir.mkdir()
        if not self.temp_dir.exists():
            self.temp_dir.mkdir()
        
        self._convert_all_document()

    def _convert_all_document(self):
        """ 转换所有笔记
        """
        index = 0
        for document in self.wiz_storage.documents:
            index += 1
            try:
                self._convert_document(document, index, len(self.wiz_storage.documents))
            except Exception:
                log.error("处理失败.", exc_info=1)

    def _convert_document(self, document: WizDocument, index: int, total: int):
        """ 转换单个笔记
        """
        if not Config.always_convert:
            is_converted = self.convertor_db.is_converted(document)
            if is_converted:
                log.debug(f"({index}/{total}) {document.location}{document.title}")
                log.debug('已处理过，跳过.')
                return

        print('')
        print(f"({index}/{total}) {document.location}{document.title}")

        # 转换前，做一些必要的检查
        if not document.file.exists():
            log.error('没找到笔记文件，请先下载！')
            log.debug(f'找不到笔记文件 `{document.file}`')
            return

        # `.ziw`笔记文件，是个压缩包，解压
        file_extract_dir = self._extract_zip(document)
        log.debug(f"解压缩路径：{file_extract_dir}")
        if file_extract_dir is None:
            return
        # 解压后的`index.html`是笔记的内容
        index_html_file = file_extract_dir.joinpath("index.html")
        if not index_html_file.exists():
            log.errorr(f"主文档文件不存在！ {index_html_file}")
            return
        
        # 默认使用笔记名做为文件名，如果因含有特殊字符而调整过，给出提示
        if document.title != document.output_file_name:
            log.debug(f"文件名含有特殊字符，已做处理 `{document.title}` -> `{document.output_file_name}`")            

        # 拼接输出文件的全路径，并创建相应文件夹
        target_file = Path(str(self.target_dir) + document.location + document.output_file_name).expanduser()
        if not target_file.parent.exists():
            target_file.parent.mkdir(parents=True)

        # 提取附件
        target_attachments_dir = Path(str(target_file) + "_Attachments")
        _convert_attachments(document, target_attachments_dir)

        # 不同笔记类型，转md
        target_file = Path(str(target_file) + ".md")
        if document.is_todolist(file_extract_dir):
            convert_td(file_extract_dir, target_file)
        else:
            markdown = wiz_html_to_md(index_html_file, document.attachments, target_attachments_dir, self.wiz_storage)
            markdown = markdown.replace("\r\n", "\n")  #避免多余的空行
            if markdown == "":
                log.warning("Markdown is empty.")
            if document.is_markdown():
                markdown = markdown.replace('\xa0',' ') #将特殊空格替换为普通空格
            target_file.write_text(markdown, "UTF-8")

        _add_front_matter_and_update_time(target_file, document)
        self.convertor_db.save_result(document.guid, True)
        print('ok')

    def _extract_zip(self, document: WizDocument) -> Path:
        """ 解压缩当前文档的 zip 文件到 work_dir，以 guid 为子文件夹名称
        """
        file_extract_dir = self.temp_dir.joinpath(document.guid)
        # 如果目标文件夹已经存在，并且解压后笔记文件没有更新，就不解压了
        if file_extract_dir.exists() and not self.convertor_db.is_modified_after_extract(document):
            return file_extract_dir

        try:
            zip_file = ZipFile(document.file)
            zip_file.extractall(file_extract_dir)
            self.convertor_db.save_extract_time(document.guid)
            return file_extract_dir
        except BadZipFile:
            log.error('解压失败，该笔记可能是加密笔记，请先解密')
