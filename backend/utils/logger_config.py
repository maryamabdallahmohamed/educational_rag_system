import logging
import logging.handlers
import queue
import os
def get_logger(name: str, log_level=logging.INFO, log_dir="logs", log_file="app.log"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if not logger.handlers:
        log_queue = queue.Queue(-1)  # infinite size
        queue_handler = logging.handlers.QueueHandler(log_queue)

        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, log_file), maxBytes=5 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
        ))

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"
        ))

        listener = logging.handlers.QueueListener(log_queue, file_handler, console_handler)
        listener.start()

        logger.addHandler(queue_handler)

    return logger
