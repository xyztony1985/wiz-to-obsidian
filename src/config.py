class Config:

    convertor_db_path = "output/convertor.db"
    """ 转换过程的数据，保存在这个数据库 """

    output_dir = "output/notes"
    """ 转换后的笔记放在这个目录 """

    temp_dir = "output/temp"
    """ 转换过程的临时文件放在这个目录 """

    always_convert = False
    """ 是否总是转换，如果为True，则不会检查笔记是否已经转换过，直接转换 """
