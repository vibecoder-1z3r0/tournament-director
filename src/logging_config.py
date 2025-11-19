"""
Logging configuration for Tournament Director.

Provides centralized logging setup with support for multiple handlers,
structured logging, and environment-specific configurations.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


# Default log format with timestamp, level, module, and message
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Detailed format for file logging (includes function name and line number)
DETAILED_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "%(filename)s:%(lineno)d - %(funcName)s - %(message)s"
)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console: bool = True,
    detailed: bool = False,
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file for persistent logging
        console: Whether to log to console (stdout)
        detailed: Use detailed format (includes file/line/function info)

    Example:
        >>> setup_logging(level="DEBUG", log_file=Path("tournament.log"))
        >>> logger = logging.getLogger("tournament")
        >>> logger.info("Tournament started")
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Select format
    formatter = logging.Formatter(
        DETAILED_FORMAT if detailed else DEFAULT_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stdout)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file is not None:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Use RotatingFileHandler to prevent huge log files
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,  # Keep 5 backup files
        )
        file_handler.setLevel(numeric_level)
        # Always use detailed format for files
        file_handler.setFormatter(logging.Formatter(DETAILED_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    return logging.getLogger(name)


def log_tournament_event(
    logger: logging.Logger,
    event: str,
    tournament_id: str,
    **context,
) -> None:
    """
    Log a tournament-related event with structured context.

    Args:
        logger: Logger instance
        event: Event description
        tournament_id: Tournament UUID
        **context: Additional context as keyword arguments

    Example:
        >>> log_tournament_event(
        ...     logger,
        ...     "Round started",
        ...     tournament_id="abc-123",
        ...     round_number=2,
        ...     player_count=8
        ... )
    """
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    logger.info(f"[Tournament {tournament_id}] {event} | {context_str}")


def log_pairing_decision(
    logger: logging.Logger,
    round_number: int,
    player1_id: str,
    player2_id: Optional[str],
    reason: str,
    **context,
) -> None:
    """
    Log a pairing decision with context.

    Args:
        logger: Logger instance
        round_number: Round number
        player1_id: First player UUID
        player2_id: Second player UUID (None for bye)
        reason: Why this pairing was made
        **context: Additional context

    Example:
        >>> log_pairing_decision(
        ...     logger,
        ...     round_number=2,
        ...     player1_id="abc",
        ...     player2_id="def",
        ...     reason="Same bracket, haven't played",
        ...     bracket=6
        ... )
    """
    opponent = player2_id if player2_id else "BYE"
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    logger.debug(
        f"[Round {round_number}] Pairing: {player1_id} vs {opponent} | "
        f"Reason: {reason} | {context_str}"
    )


# Pre-configured loggers for common modules
def get_pairing_logger() -> logging.Logger:
    """Get logger for pairing module."""
    return get_logger("tournament.swiss.pairing")


def get_standings_logger() -> logging.Logger:
    """Get logger for standings module."""
    return get_logger("tournament.swiss.standings")


def get_lifecycle_logger() -> logging.Logger:
    """Get logger for lifecycle module."""
    return get_logger("tournament.lifecycle")
