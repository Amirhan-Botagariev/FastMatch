"""
Исключения для работы с LLM.
"""


class LLMError(Exception):
    """
    Базовое исключение для ошибок LLM.
    """
    pass


class LLMInvalidResponseError(LLMError):
    """
    Исключение для невалидных ответов от LLM.
    """
    pass


class LLMTimeoutError(LLMError):
    """
    Исключение для таймаутов при работе с LLM.
    """
    pass

