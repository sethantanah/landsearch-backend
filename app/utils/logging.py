import logging
import logging.handlers
from pathlib import Path


class LoggerSetup:
    def __init__(
        self,
        log_dir: str = "logs",
        app_name: str = "app",
        log_level: int = logging.INFO,
        retention_days: int = 30,
        console_output: bool = True,
    ):
        """
        Initialize logging setup with time rotation and multiple handlers

        Args:
            log_dir (str): Directory to store log files
            app_name (str): Name of the application (used in log file names)
            log_level (int): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            retention_days (int): Number of days to keep log files
            console_output (bool): Whether to output logs to console
        """
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.log_level = log_level
        self.retention_days = retention_days
        self.console_output = console_output

        # Create logger
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(self.log_level)

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup different log handlers with their respective formatters"""
        # Clear any existing handlers
        self.logger.handlers.clear()

        # Common log format
        detailed_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(process)d | %(thread)d | "
            "%(filename)s:%(lineno)d | %(funcName)s | %(message)s"
        )

        # Simple format for console
        console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s"
        )

        # Setup time rotating file handler for general logs
        general_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.log_dir / f"{self.app_name}.log",
            when="midnight",
            interval=1,
            backupCount=self.retention_days,
            encoding="utf-8",
        )
        general_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(general_handler)

        # Setup separate handler for errors (WARNING and above)
        error_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.log_dir / f"{self.app_name}_error.log",
            when="midnight",
            interval=1,
            backupCount=self.retention_days,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)

        # Setup console handler if enabled
        if self.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        """Return the configured logger"""
        return self.logger


# Example usage and configuration
def setup_logging(
    log_dir: str = "logs",
    app_name: str = "app",
    log_level: str = "INFO",
    retention_days: int = 30,
    console_output: bool = True,
) -> logging.Logger:
    """
    Setup and return a configured logger

    Args:
        log_dir (str): Directory to store log files
        app_name (str): Name of the application
        log_level (str): Logging level as string ("DEBUG", "INFO", etc.)
        retention_days (int): Number of days to keep log files
        console_output (bool): Whether to output logs to console

    Returns:
        logging.Logger: Configured logger instance
    """
    # Convert string log level to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level_const = level_map.get(log_level.upper(), logging.INFO)

    # Initialize logger setup
    logger_setup = LoggerSetup(
        log_dir=log_dir,
        app_name=app_name,
        log_level=log_level_const,
        retention_days=retention_days,
        console_output=console_output,
    )

    return logger_setup.get_logger()
