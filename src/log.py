import logging
 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s %(name)s %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
 
# 创建 log 对象
log = logging.getLogger(__name__)
