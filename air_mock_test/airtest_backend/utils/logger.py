"""
日志工具模块

配置和管理系统日志。
"""

import os
import sys
from pathlib import Path
from loguru import logger as loguru_logger


class LoggerConfig:
    """日志配置"""
    
    # 默认日志格式
    DEFAULT_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    
    # 详细日志格式
    DETAILED_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
    
    @classmethod
    def setup_logger(cls, 
                    log_path: str = "./logs",
                    log_level: str = "INFO",
                    console_output: bool = True,
                    file_output: bool = True,
                    rotation: str = "10 MB",
                    retention: str = "7 days"):
        """
        配置日志系统
        
        Args:
            log_path: 日志文件路径
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            rotation: 日志轮转大小
            retention: 日志保留时间
        """
        # 移除默认的处理器
        loguru_logger.remove()
        
        # 创建日志目录
        if file_output:
            log_dir = Path(log_path)
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # 控制台输出
        if console_output:
            loguru_logger.add(
                sys.stdout,
                level=log_level,
                format=cls.DEFAULT_FORMAT,
                colorize=True
            )
        
        # 文件输出
        if file_output:
            # 主日志文件
            loguru_logger.add(
                f"{log_path}/app.log",
                level=log_level,
                format=cls.DETAILED_FORMAT,
                rotation=rotation,
                retention=retention,
                encoding="utf-8"
            )
            
            # 错误日志单独记录
            loguru_logger.add(
                f"{log_path}/error.log",
                level="ERROR",
                format=cls.DETAILED_FORMAT,
                rotation=rotation,
                retention=retention,
                encoding="utf-8"
            )
        
        loguru_logger.info("日志系统初始化完成")
        return loguru_logger
    
    @classmethod
    def get_logger(cls):
        """获取日志器实例"""
        return loguru_logger


# 全局日志实例
logger = loguru_logger


def setup_logging(**kwargs):
    """快捷配置日志"""
    return LoggerConfig.setup_logger(**kwargs)
