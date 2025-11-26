from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import uuid

import aiofiles


class FileStorage(ABC):
    """
    Абстракция над хранилищем файлов.
    """

    @abstractmethod
    async def save(self, data: bytes, filename: str) -> str:
        """
        Сохраняет файл и возвращает строковый идентификатор/путь.
        """
        raise NotImplementedError


class DiskFileStorage(FileStorage):
    """
    Хранилище, сохраняющее файлы на диск.
    """

    def __init__(self, base_dir: str = "storage/resumes") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, data: bytes, filename: str) -> str:
        # 1. Очищаем имя — убираем возможные '../' и т.п.
        safe_name = Path(filename).name

        # 2. Достаём расширение (включая точку), например ".pdf" или ".docx"
        ext = Path(safe_name).suffix.lower()  # может быть "" если расширения нет

        # 3. Генерируем UUID и используем его как базовое имя файла
        file_id = uuid.uuid4()
        disk_name = f"{file_id}{ext}"  # например "uuid.pdf"

        target_path = self.base_dir / disk_name

        # 4. Пишем данные асинхронно, чтобы не блокировать event loop
        async with aiofiles.open(target_path, "wb") as f:
            await f.write(data)

        # 5. Возвращаем строковый путь до файла
        #    (в твоём текущем коде BaseResume.file_path как раз это и хранит)
        return str(target_path)