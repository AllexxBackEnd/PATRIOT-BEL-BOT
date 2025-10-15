import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger():
    """
    Настраивает и возвращает логгер с ротацией файлов

    Returns:
        logging.Logger: Настроенный логгер
    """
    # Создаем папку для логов если ее нет
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Создаем логгер
    logger = logging.getLogger("bot_logger")
    logger.setLevel(logging.INFO)

    # Формат логов
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Файловый обработчик с ротацией
    log_file = os.path.join(log_dir,
                            f"bot_{datetime.now().strftime('%Y%m')}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
