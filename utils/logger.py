"""
Logging utility for trading bot.

Creates separate log files for each strategy, making it easy to track
what each strategy is doing independently.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_strategy_logger(strategy_instance, log_dir: str = "logs") -> logging.Logger:
    """
    Set up a logger for a specific strategy instance.
    
    Creates a log file named after the strategy class in the logs directory.
    Log files are named: {StrategyClassName}_{timestamp}.log
    
    Args:
        strategy_instance: The strategy instance to create a logger for
        log_dir: Directory to store log files (default: "logs")
    
    Returns:
        Configured logger instance for the strategy
    """
    # Get strategy class name
    strategy_name = strategy_instance.__class__.__name__
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{strategy_name}_{timestamp}.log"
    log_filepath = log_path / log_filename
    
    # Create logger for this strategy
    logger = logging.getLogger(f"strategy.{strategy_name}")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(log_filepath, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    
    # Create console handler (optional - also log to console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log initialization
    logger.info(f"=" * 60)
    logger.info(f"Strategy Logger Initialized: {strategy_name}")
    logger.info(f"Log file: {log_filepath}")
    logger.info(f"=" * 60)
    
    return logger


def get_strategy_logger(strategy_instance) -> logging.Logger:
    """
    Get the logger for a strategy instance.
    
    If logger doesn't exist, creates one. This allows strategies
    to access their logger easily.
    
    Args:
        strategy_instance: The strategy instance
    
    Returns:
        Logger instance for the strategy
    """
    strategy_name = strategy_instance.__class__.__name__
    logger_name = f"strategy.{strategy_name}"
    
    logger = logging.getLogger(logger_name)
    
    # If logger has no handlers, set it up
    if not logger.handlers:
        logger = setup_strategy_logger(strategy_instance)
    
    return logger
