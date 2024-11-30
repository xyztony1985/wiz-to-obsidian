import logging
 
logging.basicConfig(
    level=logging.INFO,

    # 详细版日志输出，转换出错时用，方便排错
    # format='%(asctime)s - %(levelname)s %(name)s %(filename)s:%(lineno)d - %(message)s',
    
    # 简洁版日志输出
    format='%(levelname)s: %(message)s',

    datefmt='%Y-%m-%d %H:%M:%S'
)
 
# 创建 log 对象
log = logging.getLogger(__name__)
