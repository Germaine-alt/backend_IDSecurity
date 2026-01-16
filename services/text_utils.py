import unicodedata
import re
from functools import lru_cache
from typing import Tuple, Optional
import datetime

# Précompile regex pour la performance
_RE_NON_ALNUM = re.compile(r"[^A-Z0-9\s\-]")
_RE_WS = re.compile(r"\s+")
_RE_DIGITS = re.compile(r"\d")

def clean_text_for_matching(text: str) -> str:
    """
    Normalise le texte OCR pour le fuzzy matching:
    - supprime accents, met en MAJUSCULE, garde lettres/chiffres/espace/tiret
    - réduit les espaces multiples
    """
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode(errors='ignore')
    text = text.upper()
    text = _RE_NON_ALNUM.sub(" ", text)
    text = _RE_WS.sub(" ", text)
    return text.strip()

def contains_digits(text: str) -> bool:
    return bool(_RE_DIGITS.search(text))

# Petit utilitaire pour formater dates détectées
def normalize_date_str(s: str) -> Optional[str]:
    """
    Essaie d'extraire/normaliser une date du texte OCR (JJ/MM/AAAA, AAAA-MM-JJ, ...).
    Retourne 'YYYY-MM-DD' ou None.
    """
    if not s:
        return None
    # garder seulement chiffres et séparateurs
    candidate = re.sub(r"[^0-9\/\-\.\s]", " ", s)
    candidate = re.sub(r"\s+", " ", candidate).strip()

    # tester plusieurs formats communs
    patterns = [
        ("%d/%m/%Y", r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
        ("%d-%m-%Y", r"\b\d{1,2}-\d{1,2}-\d{4}\b"),
        ("%Y-%m-%d", r"\b\d{4}-\d{1,2}-\d{1,2}\b"),
        ("%d.%m.%Y", r"\b\d{1,2}\.\d{1,2}\.\d{4}\b")
    ]
    for fmt, regex in patterns:
        m = re.search(regex, candidate)
        if m:
            try:
                dt = datetime.datetime.strptime(m.group(0), fmt)
                return dt.date().isoformat()
            except Exception:
                continue
    return None