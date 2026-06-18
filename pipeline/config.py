"""
Configuration module for A/B test analytics project.
Handles paths, thresholds, and analysis parameters.
"""
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Settings:
    """Main settings class for the project."""
    
    # Paths
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = None
    output_dir: Path = None
    sql_dir: Path = None
    db_path: Path = None
    
    # Analysis parameters
    confidence_level: float = 0.95
    significance_level: float = 0.05
    min_sample_size: int = 100
    
    # CUPED parameters
    use_cuped: bool = True
    cuped_covariate_window_days: int = 7
    
    # Cohort analysis
    cohort_window_days: int = 7
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Data validation
    validate_data: bool = True
    max_missing_pct: float = 0.05
    
    def __post_init__(self):
        """Initialize derived paths."""
        if self.data_dir is None:
            self.data_dir = self.project_root / "data"
        if self.output_dir is None:
            self.output_dir = self.project_root / "reports"
        if self.sql_dir is None:
            self.sql_dir = self.project_root / "sql"
        if self.db_path is None:
            self.db_path = self.data_dir / "ab_test.db"


def setup_logging(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    Configure and return a logger.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (defaults to settings.log_level)
        log_file: Optional file to log to
        
    Returns:
        Configured logger instance
    """
    settings_obj = Settings()
    log_level = level or settings_obj.log_level
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    formatter = logging.Formatter(settings_obj.log_format)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Global settings instance
settings = Settings()
