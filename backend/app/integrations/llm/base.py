from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMClient(ABC):
    @abstractmethod
    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Сгенерировать JSON на основе промпта.
        """
        raise NotImplementedError