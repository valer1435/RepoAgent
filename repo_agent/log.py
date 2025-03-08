import inspect
import logging
import sys
from loguru import logger
logger = logger.opt(colors=True)
'\nRepoAgent 日志记录器对象。\n\n默认信息:\n- 格式: `[%(asctime)s %(name)s] %(levelname)s: %(message)s`\n- 等级: `INFO` ，根据 `CONFIG["log_level"]` 配置改变\n- 输出: 输出至 stdout\n\n用法示例:\n    ```python\n    from repo_agent.log import logger\n    \n    # 基本消息记录\n    logger.info("It <green>works</>!") # 使用颜色\n\n    # 记录异常信息\n    try:\n        1 / 0\n    except ZeroDivisionError:\n        # 使用 `logger.exception` 可以在记录异常消息时自动附加异常的堆栈跟踪信息。\n        logger.exception("ZeroDivisionError occurred")\n\n    # 记录调试信息\n    logger.debug(f"Debugging info: {some_debug_variable}")\n\n    # 记录警告信息\n    logger.warning("This is a warning message")\n\n    # 记录错误信息\n    logger.error("An error occurred")\n    ```\n\n'

class InterceptHandler(logging.Handler):
    """# Repository Documentation Generator: InterceptHandler Method

The InterceptHandler method is a custom logging handler within the Repository Documentation Generator project, facilitating seamless integration between Python's standard logging module and loguru, a more feature-rich logging library. This method captures log records from the standard logging module and forwards them to loguru for processing, ensuring consistent handling of logs across the application.

## Long Description

The InterceptHandler method, an instance of `logging.Handler`, overrides its `emit` method. When a log record is emitted, this method retrieves the corresponding log level (either from loguru or the standard logging level) and finds the caller's information using Python's inspect module. It then logs the message with the determined level and exception details to loguru, providing a consistent logging experience while leveraging loguru's advanced features.

## Args

record (logging.LogRecord): The log record emitted by the standard logging module.

## Returns

None

## Raises

None

## Note

See also: `set_logger_level_from_config` for an example of how to configure and use this InterceptHandler method in conjunction with loguru within the Repository Documentation Generator project. This method plays a crucial role in managing logging and error handling, contributing to the overall seamless operation of the tool."""

    def emit(self, record: logging.LogRecord) -> None:
        """'''
Configures the loguru logger with specified log level and integrates it with the standard logging module.

This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It ensures consistent and up-to-date logging across the application, facilitating seamless operation and error handling.

Args:
    log_level (str): The log level to set for loguru (e.g., "DEBUG", "INFO", "WARNING"). This parameter determines the verbosity of logged messages.

Returns:
    None

Raises:
    None

Note:
    This function does not return any value but configures the logging system, ensuring all logs are handled consistently by loguru.

    See also: repo_agent\\log.py/InterceptHandler for an example of how this function integrates with a custom logging handler within the Repository Documentation Generator.
'''"""
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
    '''"""Emits a log record using Loguru within the Repository Documentation Generator project.

This function, part of the InterceptHandler class in repo_agent/log.py, takes a logging.LogRecord object as input and logs it using the Loguru logger. It first attempts to map the logging level to its corresponding Loguru level. If this fails, it uses the original logging level. Then, it determines the caller of the logged message by tracing back through the call stack until it finds a frame not originating from the logging module. Finally, it logs the message with the determined level and any exception information.

This function is instrumental in managing the logging capabilities of the Repository Documentation Generator, ensuring that all relevant activities are accurately recorded for documentation purposes.

Args:
    record (logging.LogRecord): The log record to be emitted. This could include details such as the log message, timestamp, and other metadata associated with the logged event.

Returns:
    None: This function does not return any value. Its purpose is to emit the log record immediately.

Raises:
    ValueError: If the logging level cannot be mapped to a Loguru level. This ensures that all logged messages adhere to a consistent format, facilitating easier interpretation and analysis of logs during documentation generation.

Note:
    This function operates within the broader context of the Repository Documentation Generator project, which automates the documentation process for software projects using advanced techniques such as chat-based interaction and multi-task dispatching. It leverages both Python's logging and Loguru libraries to provide enhanced logging capabilities, contributing to the overall reliability and traceability of the documentation generation workflow.
"""'''
    logger.remove()
    logger.add(sys.stderr, level=log_level, enqueue=True, backtrace=False, diagnose=False)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    logger.success(f'Log level set to {log_level}!')