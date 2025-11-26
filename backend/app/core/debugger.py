from __future__ import annotations

import dataclasses
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypeVar

from app.core.config import settings
from pydantic import BaseModel

T = TypeVar("T")


@dataclass
class DebugSnapshot:
    """
    Снимок состояния в момент вызова debug():
      - метка (label)
      - тип объекта
      - сериализованное значение
      - стек вызовов в удобном виде
    """
    label: str
    type_name: str
    value: Any
    trace: List[Dict[str, Any]]


class DebugStop(Exception):
    """
    Специальное исключение, которое выбрасывается при вызове debug()
    в режиме DEBUG=true.

    Его будет перехватывать глобальный обработчик и рендерить HTML-страницу.
    """

    def __init__(self, snapshot: DebugSnapshot) -> None:
        self.snapshot = snapshot
        super().__init__(f"Debug stop: {snapshot.label or snapshot.type_name}")


class Debugger:
    """
    Центральный механизм дебага.

    Методы:
      - snapshot(value, label) -> DebugSnapshot
      - stop(value, label) -> поднимает DebugStop (если DEBUG=true)
      - debug(value, label) -> удобный wrapper, который либо стопает,
                               либо просто возвращает value без побочек.
    """

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def _serialize_value(self, value: Any) -> Any:
        """
        Аккуратно сериализует значение для вывода на debug-страницу.
        Чтобы не падать, если там какие-то странные объекты.
        """
        try:
            if dataclasses.is_dataclass(value):
                return dataclasses.asdict(value)

            if isinstance(value, BaseModel):
                # Pydantic v2
                return value.model_dump()

            if isinstance(value, (str, int, float, bool)) or value is None:
                return value

            if isinstance(value, (list, tuple)):
                return [self._serialize_value(v) for v in value]

            if isinstance(value, dict):
                return {str(k): self._serialize_value(v) for k, v in value.items()}

            return repr(value)
        except Exception as exc:
            return f"<unserializable: {exc!r}>"

    def snapshot(self, value: Any, label: Optional[str] = None) -> DebugSnapshot:
        """
        Собирает снимок состояния: объект + стек вызовов.
        Ничего не логирует и не останавливает выполнение.
        """
        stack = traceback.extract_stack()[:-1]
        last_frames = stack[-10:]  # ограничим глубину

        trace: List[Dict[str, Any]] = []
        for frame in reversed(last_frames):
            trace.append(
                {
                    "file": frame.filename,
                    "line": frame.lineno,
                    "function": frame.name,
                    "code": (frame.line or "").strip(),
                }
            )

        return DebugSnapshot(
            label=label or "",
            type_name=type(value).__name__,
            value=self._serialize_value(value),
            trace=trace,
        )

    def stop(self, value: Any, label: Optional[str] = None) -> None:
        """
        Жёсткий стоп: всегда поднимает DebugStop (если enabled=true).
        Если enabled=false — ничего не делает.
        """
        if not self.enabled:
            return

        snapshot = self.snapshot(value, label=label)
        raise DebugStop(snapshot)

    def debug(self, value: T, label: Optional[str] = None) -> T:
        """
        Основной метод, который ты будешь использовать в коде.

        Если DEBUG=true:
          - собирает snapshot
          - поднимает DebugStop → endpoint останавливается, возвращаем debug HTML.

        Если DEBUG=false:
          - просто возвращает value и ничего не делает
          - никаких логов, никаких исключений
        """
        if not self.enabled:
            return value

        snapshot = self.snapshot(value, label=label)
        raise DebugStop(snapshot)


# Глобальный инстанс, привязанный к настройке DEBUG
debugger = Debugger(enabled=settings.DEBUG)


def debug(value: T, label: Optional[str] = None) -> T:
    """
    Удобная глобальная функция.

    В коде можно писать просто:
        result = debug(result, "после парсинга резюме")

    А под капотом она либо остановит выполнение и покажет страницу,
    либо ничего не сделает (если DEBUG=false).
    """
    return debugger.debug(value, label=label)