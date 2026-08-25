import logging
import sys

# 日志工具，方便调试节点执行过程。
def setup_logger(name: str = "PersonalAssistant") -> logging.Logger:
    logger = logging.getLogger(name)
    # 防止重复添加处理器Python
    if not logger.handlers:
        # 设置输出位置
        handler = logging.StreamHandler(sys.stdout)
        # 设置日志格式
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(handler)
        # 设置日志级别
        logger.setLevel(logging.INFO)
    return logger
