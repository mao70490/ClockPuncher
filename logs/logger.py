import logging

def setup_logger(log_name: str = __name__, log_file: str = "logs/puncher.log"):
    """建立並回傳 logger"""
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)  # 設定最低級別

    # 避免重複加入 handler
    if not logger.handlers:
        # 檔案 handler
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.INFO)

        # console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # 格式
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
