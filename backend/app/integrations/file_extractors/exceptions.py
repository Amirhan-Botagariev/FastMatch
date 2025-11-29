class UnsupportedFileFormatError(Exception):
    """
    Исключение для неподдерживаемых форматов файлов.
    Его обычно перехватывает верхний слой и отдаёт 400/422.
    """
    pass

