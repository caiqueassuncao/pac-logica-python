import pygame

LOGIC_GLYPHS = "∧∨→↔¬"
TEXT_GLYPHS = "ÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç×·"
ASCII_LOGIC = str.maketrans({"∧": "^", "∨": "v", "→": "->", "↔": "<->", "¬": "~", "×": "x", "·": "-"})

# Primeira fonte instalada que tiver todos os glifos necessários (Windows, macOS, Linux).
UI_FONTS = [("segoeuisemibold", False), ("helveticaneue", False), ("helvetica", False),
            ("ubuntu", False), ("cantarell", False), ("notosans", False),
            ("dejavusans", False), ("liberationsans", False), ("arial", False)]
TITLE_FONTS = [("segoeuiblack", False), ("segoeui", True), ("helveticaneue", True),
               ("arialblack", False), ("ubuntu", True), ("notosans", True),
               ("dejavusans", True), ("arial", True)]
LOGIC_FONTS = [("segoeuisymbol", False), ("dejavusans", False), ("lucidagrande", False),
               ("arialunicodems", False), ("menlo", False), ("notosansmath", False),
               ("stixgeneral", False), ("freesans", False), ("cambriamath", False)]

def supports(font, chars):
    """True se a fonte tem todos os glifos (glifos ausentes têm as métricas do 'tofu')."""
    tofu = font.metrics("")[0]
    return all(m is not None and m != tofu for m in font.metrics(chars))

def pick_font(candidates, chars):
    for name, bold in candidates:
        path = pygame.font.match_font(name, bold=bold)
        if not path:
            continue
        try:
            if supports(pygame.font.Font(path, 20), chars):
                return path
        except (OSError, pygame.error):
            continue
    return None

class FontBook:
    def __init__(self):
        self.ui = pick_font(UI_FONTS, TEXT_GLYPHS)
        self.title = pick_font(TITLE_FONTS, TEXT_GLYPHS) or self.ui
        self.logic = pick_font(LOGIC_FONTS, LOGIC_GLYPHS + TEXT_GLYPHS)
        self._cache = {}

    def get(self, size, bold=False, logic=False):
        path = self.logic if logic else (self.title if bold else self.ui)
        key = (path, size, bold)
        if key not in self._cache:
            font = pygame.font.Font(path, size)
            if bold and path == self.ui:
                font.set_bold(True)
            self._cache[key] = font
        return self._cache[key]

    def prepare(self, text, size, bold=False):
        """Escolhe a fonte adequada ao texto; sem fonte com símbolos lógicos, usa ASCII."""
        if any(ch in LOGIC_GLYPHS for ch in text):
            if self.logic:
                return self.get(size, logic=True), text
            text = text.translate(ASCII_LOGIC)
        return self.get(size, bold), text
