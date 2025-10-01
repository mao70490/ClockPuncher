import logging, os, atexit
from concurrent_log_handler import ConcurrentTimedRotatingFileHandler

def setup_logger(log_name: str = __name__, log_file_base: str = "logs/puncher.log"):
    """
    建立並回傳 logger
    log 會每天午夜輪替，檔名自動加日期，最多保留 5 天
    """
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    # 確保 logs 資料夾存在
    os.makedirs(os.path.dirname(log_file_base), exist_ok=True)

    if not logger.handlers:
        # 每天午夜輪替
        fh = ConcurrentTimedRotatingFileHandler(
            log_file_base,
            when="midnight",
            interval=1,
            backupCount=5,
            encoding="utf-8"
        )
        # 設定檔名後綴為日期
        # fh.suffix = "%Y%m%d"  # 生成檔名像 puncher.log.20250927
        fh.setLevel(logging.INFO)

        # console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # log 格式
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        # 註冊程式結束時自動釋放
        atexit.register(logging.shutdown)

    return logger
