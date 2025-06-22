import inspect
import logging
import sys
from loguru import logger
logger = logger.opt(colors=True)
'\nRepoAgent 日志记录器对象。\n\n默认信息:\n- 格式: `[%(asctime)s %(name)s] %(levelname)s: %(message)s`\n- 等级: `INFO` ，根据 `CONFIG["log_level"]` 配置改变\n- 输出: 输出至 stdout\n\n用法示例:\n    ```python\n    from repo_agent.log import logger\n    \n    # 基本消息记录\n    logger.info("It <green>works</>!") # 使用颜色\n\n    # 记录异常信息\n    try:\n        1 / 0\n    except ZeroDivisionError:\n        # 使用 `logger.exception` 可以在记录异常消息时自动附加异常的堆栈跟踪信息。\n        logger.exception("ZeroDivisionError occurred")\n\n    # 记录调试信息\n    logger.debug(f"Debugging info: {some_debug_variable}")\n\n    # 记录警告信息\n    logger.warning("This is a warning message")\n\n    # 记录错误信息\n    logger.error("An error occurred")\n    ```\n\n'

class InterceptHandler(logging.Handler):
    """
    InterceptHandler is a custom logging handler that intercepts log records and forwards them to a logger with the appropriate log level and depth.
    
    This handler is designed to work with a logger that supports custom log levels and depth settings, such as the one provided by the `loguru` library. It ensures that log records are emitted with the correct context and formatting, which is crucial for maintaining accurate and detailed logs in the `repo_agent` project's automated documentation generation and management system.
    
    Note:
        This handler is used in conjunction with the `set_logger_level_from_config` function to configure the logging level and intercept log records. It plays a vital role in the project's logging infrastructure, ensuring that all log messages are consistent and contextually accurate.
    
    ---
    
    emit emits a log record to the logger.
    
    Args:
        record (logging.LogRecord): The log record to be emitted.
    
    Returns:
        None: This method does not return any value.
    
    Raises:
        ValueError: If the log level name cannot be found in the logger's levels.
    
    Note:
        This method uses the `inspect` module to determine the correct stack depth for the log message. The `repo_agent` project automates the generation and management of documentation for Python projects within a Git repository, ensuring that the documentation remains up-to-date and accurately reflects the current state of the codebase. It leverages Git to detect changes, manage file handling, and generate documentation summaries, while also providing a command-line interface (CLI) for easy interaction. Additionally, it supports multi-threaded task management and configuration settings to customize the documentation generation process.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
    Sets the logger level based on the provided configuration.
    
    This method configures the logging level for the application by removing existing log handlers and adding a new one with the specified log level. It also sets up the basic configuration for the logging system to use the custom `InterceptHandler`.
    
    Args:
        log_level (str): The log level to set. This should be a valid log level name such as 'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'.
    
    Returns:
        None: This method does not return any value.
    
    Raises:
        ValueError: If the log level name cannot be found in the logger's level mapping.
    
    Note:
        This method is used in conjunction with the `InterceptHandler` to ensure that log records are emitted with the correct context and formatting. It is called in the `run` and `run_outside_cli` methods of the `main.py` module to configure the logging level based on user input. This is crucial for the `repo_agent` project's ability to automate the generation and management of documentation for a Git repository, ensuring that logging is consistent and informative.
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
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def set_logger_level_from_config(log_level):
    """
    Emits a log record to the logger.
    
    This method processes a log record and emits it to the logger with the appropriate level and depth. It ensures that the log message is formatted correctly and includes any exception information if available. This is particularly useful for maintaining accurate and detailed logs during the automated generation and management of documentation for a Git repository.
    
    Args:
        record (logging.LogRecord): The log record to be emitted.
    
    Returns:
        None: This method does not return any value.
    
    Raises:
        ValueError: If the log level name cannot be found in the logger's levels.
    
    Note:
        This method uses the `inspect` module to determine the correct stack depth for the log message. The `repo_agent` project automates the generation and management of documentation for Python projects within a Git repository, ensuring that the documentation remains up-to-date and accurately reflects the current state of the codebase. It leverages Git to detect changes, manage file handling, and generate documentation summaries, while also providing a command-line interface (CLI) for easy interaction. Additionally, it supports multi-threaded task management and configuration settings to customize the documentation generation process.
    """
    logger.remove()
    logger.add(sys.stderr, level=log_level, enqueue=True, backtrace=False, diagnose=False)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    logger.success(f'Log level set to {log_level}!')