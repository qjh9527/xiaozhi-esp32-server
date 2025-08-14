import os
import sys
from loguru import logger
from config.config_loader import load_config
from config.settings import check_config_file
from datetime import datetime

SERVER_VERSION = "0.7.5"
_logger_initialized = False


def generate_log_filename(prefix_dir: str = ".") -> str:
    """
    生成形如 2025_0813.0.log 的日志文件名。
    前缀为当天日期，后缀数字为当天已存在文件的最大序号 +1。

    :param prefix_dir: 日志文件所在目录，默认当前目录
    :return: 完整的日志文件名（不含路径）
    """
    today_str = datetime.now().strftime("%Y_%m%d")

    # 已存在且符合当日命名规则的文件
    existing = [
        f for f in os.listdir(prefix_dir)
        if f.startswith(today_str) and f.endswith(".log")
    ]

    # 提取序号，默认为 -1 方便后续 +1
    max_n = -1
    for name in existing:
        # 形如 2025_0813.7.log -> 7
        try:
            n = int(name[len(today_str) + 1:-4])
            max_n = max(max_n, n)
        except ValueError:
            continue

    next_n = max_n + 1
    return f"{today_str}.{next_n}.log"

def get_module_abbreviation(module_name, module_dict):
    """获取模块名称的缩写，如果为空则返回00
    如果名称中包含下划线，则返回下划线后面的前两个字符
    """
    module_value = module_dict.get(module_name, "")
    if not module_value:
        return "00"
    if "_" in module_value:
        parts = module_value.split("_")
        return parts[-1][:2] if parts[-1] else "00"
    return module_value[:2]


def build_module_string(selected_module):
    """构建模块字符串"""
    return (
        get_module_abbreviation("VAD", selected_module)
        + get_module_abbreviation("ASR", selected_module)
        + get_module_abbreviation("LLM", selected_module)
        + get_module_abbreviation("TTS", selected_module)
        + get_module_abbreviation("Memory", selected_module)
        + get_module_abbreviation("Intent", selected_module)
        + get_module_abbreviation("VLLM", selected_module)
    )


def formatter(record):
    """为没有 tag 的日志添加默认值，并处理动态模块字符串"""
    record["extra"].setdefault("tag", record["name"])
    # 如果没有设置 selected_module，使用默认值
    record["extra"].setdefault("selected_module", "00000000000000")
    # 将 selected_module 从 extra 提取到顶级，以支持 {selected_module} 格式
    record["selected_module"] = record["extra"]["selected_module"]
    return record["message"]


def setup_logging():
    check_config_file()
    """从配置文件中读取日志配置，并设置日志输出格式和级别"""
    config = load_config()
    log_config = config["log"]
    global _logger_initialized

    # 第一次初始化时配置日志
    if not _logger_initialized:
        # 使用默认的模块字符串进行初始化
        logger.configure(
            extra={
                "selected_module": log_config.get("selected_module", "00000000000000"),
            }
        )

        log_format = log_config.get(
            "log_format",
            "<green>{time:YYMMDD HH:mm:ss}</green>[{version}_{extra[selected_module]}][<light-blue>{extra[tag]}</light-blue>]-<level>{level}</level>-<light-green>{message}</light-green>",
        )
        log_format_file = log_config.get(
            "log_format_file",
            "{time:YYYY-MM-DD HH:mm:ss} - {version}_{extra[selected_module]} - {name} - {level} - {extra[tag]} - {message}",
        )
        log_format = log_format.replace("{version}", SERVER_VERSION)
        log_format_file = log_format_file.replace("{version}", SERVER_VERSION)

        log_level = log_config.get("log_level", "INFO")
        log_dir = log_config.get("log_dir", "tmp")
        os.makedirs(log_dir, exist_ok=True)
        log_file = generate_log_filename(log_dir)
        data_dir = log_config.get("data_dir", "data")

        os.makedirs(data_dir, exist_ok=True)

        # 配置日志输出
        logger.remove()

        # 输出到控制台
        logger.add(sys.stdout, format=log_format, level=log_level, filter=formatter)

        # 输出到文件 - 统一目录，按大小轮转
        # 日志文件完整路径
        log_file_path = os.path.join(log_dir, log_file)

        # 添加日志处理器
        logger.add(
            log_file_path,
            format=log_format_file,
            level=log_level,
            filter=formatter,
            rotation="10 MB",  # 每个文件最大10MB
            retention="30 days",  # 保留30天
            compression=None,
            encoding="utf-8",
            enqueue=True,  # 异步安全
            backtrace=True,
            diagnose=True,
        )
        _logger_initialized = True  # 标记为已初始化

    return logger


def create_connection_logger(selected_module_str):
    """为连接创建独立的日志器，绑定特定的模块字符串"""
    return logger.bind(selected_module=selected_module_str)
