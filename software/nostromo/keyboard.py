"""
Nostromo Terminal — keyboard layout handler.
EN/RU toggle via Tab key.
"""

EN_TO_RU = {
    'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е',
    'y': 'н', 'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з',
    '[': 'х', ']': 'ъ', 'a': 'ф', 's': 'ы', 'd': 'в',
    'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л',
    'l': 'д', ';': 'ж', "'": 'э', 'z': 'я', 'x': 'ч',
    'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь',
    ',': 'б', '.': 'ю', '`': 'ё',
}


class KeyboardLayout:
    """Handles EN/RU keyboard layout switching."""

    def __init__(self):
        self.layout = "en"

    def toggle(self):
        self.layout = "ru" if self.layout == "en" else "en"

    @property
    def is_ru(self):
        return self.layout == "ru"

    @property
    def label(self):
        return "RU" if self.is_ru else "EN"

    def translate(self, char):
        """Translate a character according to current layout."""
        if self.is_ru:
            return EN_TO_RU.get(char.lower(), char)
        return char
