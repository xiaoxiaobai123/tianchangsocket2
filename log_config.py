import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger('my_application_logger')
    logger.setLevel(logging.DEBUG)

    # 检查是否已经添加了 RotatingFileHandler
    if not any(isinstance(handler, RotatingFileHandler) for handler in logger.handlers):
        # 创建一个 RotatingFileHandler
        handler = RotatingFileHandler('my_app.log', maxBytes=1024*1024*5, backupCount=5)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger

