# -*- coding: utf-8 -*-
"""Wspólne pomocnicze funkcje tekstowe (emoji)."""
import re
# emoji i znaki z nimi łączone: piktogramy, symbole, łączniki ZWJ, selektory wariantu, odcienie skóry, flagi
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\uFE0E\uFE0F\u200D\u20E3\U000E0020-\U000E007F]")
def strip_emoji(s):
    """Tekst bez emoji (do filtra słów i do syntezy mowy)."""
    return EMOJI_RE.sub("", str(s or ""))
_SURR = re.compile("[\ud800-\udfff]")
def fix_surrogates(o):
    """Usuwa samotne połówki par UTF-16 (np. emoji ucięte po stronie klienta) – inaczej zapis UTF-8 by się wywrócił."""
    if isinstance(o, str): return _SURR.sub("", o) if _SURR.search(o) else o
    if isinstance(o, list): return [fix_surrogates(x) for x in o]
    if isinstance(o, dict): return {fix_surrogates(k): fix_surrogates(v) for k, v in o.items()}
    return o
