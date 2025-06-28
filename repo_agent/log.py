import inspect
import logging
import sys
from loguru import logger

logger = logger.opt(colors=True)
'\nRepoAgent 日志记录器对象。\n\n默认信息:\n- 格式: `[%(asctime)s %(name)s] %(levelname)s: %(message)s`\n- 等级: `INFO` ，根据 `CONFIG["log_level"]` 配置改变\n- 输出: 输出至 stdout\n\n用法示例:\n    ```python\n    from repo_agent.log import logger\n    \n    # 基本消息记录\n    logger.info("It <green>works</>!") # 使用颜色\n\n    # 记录异常信息\n    try:\n        1 / 0\n    except ZeroDivisionError:\n        # 使用 `logger.exception` 可以在记录异常消息时自动附加异常的堆栈跟踪信息。\n        logger.exception("ZeroDivisionError occurred")\n\n    # 记录调试信息\n    logger.debug(f"Debugging info: {some_debug_variable}")\n\n    # 记录警告信息\n    logger.warning("This is a warning message")\n\n    # 记录错误信息\n    logger.error("An error occurred")\n    ```\n\n'


class InterceptHandler(logging.Handler):
    """
    Handles logging records with adjusted backtrace depth.

        This handler is designed to work with loguru and modifies the
        backtrace of each record before logging, removing frames related to
        the logging module itself for cleaner and more informative logs.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
        Logs a record, adjusting the call stack depth to exclude internal logging frames.

            This method adjusts the backtrace depth to exclude frames from the logging
            module itself, providing more relevant context in logs. It then uses
            loguru's logger to log the record at the appropriate level.

            Args:
                record: The logging record to emit.

            Returns:
                None
        """

        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = (inspect.currentframe(), 0)
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def set_logger_level_from_config(log_level):
    """
    Sets the logger level based on the provided configuration.

        Args:
            log_level: The desired log level (e.g., "DEBUG", "INFO", "WARNING").

        Returns:
            None
    """
    logger.remove()
    logger.add(
        sys.stderr, level=log_level, enqueue=True, backtrace=False, diagnose=False
    )
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    logger.success(f"Log level set to {log_level}!")
