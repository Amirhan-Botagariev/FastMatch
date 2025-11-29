from __future__ import annotations

import logging
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class LogConfig:
    """
    Конфигурация логгера приложения.
    """
    name: str = "FastMatch"
    level: int = logging.INFO
    propagate: bool = False


class AppLogger:
    """
    Обёртка над стандартным logging.Logger.

    Делает:
      - настройку вывода в stdout
      - настройку вывода в файл <project_root>/log/app.log
      - удобный метод exception() для логирования ошибок с трейсом
    """

    def __init__(self, config: Optional[LogConfig] = None) -> None:
        self._config = config or LogConfig()
        self._logger = logging.getLogger(self._config.name)
        self._configure_logger()

    def _get_log_file_path(self) -> Path:
        """
        Определяем путь до файла логов:
          <project_root>/log/app.log

        Где <project_root> — корень проекта (на один уровень выше backend).
        """
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[3]  # .../FastMatch
        log_dir = project_root / "log"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "app.log"

    def _configure_logger(self) -> None:
        self._logger.setLevel(self._config.level)
        self._logger.propagate = self._config.propagate

        if self._logger.handlers:
            # Уже настроен где-то — не дублируем
            return

        # ---- Handler в stdout ----
        stream_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stream_handler.setFormatter(formatter)
        self._logger.addHandler(stream_handler)

        # ---- Handler в файл ----
        file_path = self._get_log_file_path()
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    # ---- Базовые уровни ----

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error(msg, *args, **kwargs)

    def exception(
        self,
        exc: BaseException,
        message: str | None = None,
        **extra: Any,
    ) -> None:
        """
        Логирует исключение с полным stack trace и дополнительным контекстом.
        """
        base_msg = message or "Unhandled exception"
        exc_type = type(exc).__name__
        exc_text = str(exc)

        tb_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        full_msg = (
            f"{base_msg} | exception={exc_type}: {exc_text} "
            f"| trace:\n{tb_text}"
        )

        if extra:
            full_msg += f"\nextra={extra!r}"

        self._logger.error(full_msg)


# Глобальный логгер
app_logger = AppLogger()

