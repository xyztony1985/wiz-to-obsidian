from pathlib import Path
from convertor_db import ConvertorDB
from wiz.wiz_db import WizDB
from wiz.wiz_storage import WizStorage
from wiz.wiz_convertor import WizConvertor

# 获取为知笔记的数据目录
wiz_dir = input("笔记文件夹参考：C:\\Users\\windows用户名\\Documents\\My Knowledge\\Data\\为知账号名\n输入为知笔记文件夹路径：")
wiz_dir = Path(wiz_dir).expanduser()
print(f'\n\n账号:{wiz_dir.name}')


# 初始化几个重要对象
wiz_db = WizDB(wiz_dir)
convertor_db = ConvertorDB()
wiz_storage = WizStorage(wiz_dir, wiz_db, convertor_db)

# 启动转换器
WizConvertor(convertor_db, wiz_storage)
