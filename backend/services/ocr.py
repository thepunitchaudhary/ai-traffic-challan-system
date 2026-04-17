import easyocr

# Lazy-loaded singleton to avoid re-initializing on every request
_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def read_plate(image_path: str) -> str | None:
    """Read plate text from cropped plate image."""
    reader = _get_reader()
    result = reader.readtext(image_path)

    if len(result) > 0:
        text = result[0][-2]
        # Clean: remove spaces, uppercase
        return text.replace(" ", "").upper()

    return None
