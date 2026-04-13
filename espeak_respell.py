"""Respell YIVO romanization for German espeak phonemizer.

German espeak misinterprets many YIVO romanization patterns. This module
converts YIVO romanized Yiddish into spellings that make German espeak
produce the correct phonemes.

The transforms are pure string operations — easy to port to Swift/Kotlin
for on-device TTS.

Mapping summary (YIVO romanization → German-espeak spelling):
    Consonants:
        sh  → sch      (but "sht" at word start → "st", "shp" → "sp")
        zh  → j        (German j before vowels = ʒ in loanwords, "journal")
        tsh → tsch
        kh  → ch
        ts  → z        (German z = [ts])
        z   → s        (German s before vowel = [z])
    Vowels/diphthongs:
        ey  → ej
        ay  → aj
        oy  → oj
    Everywhere:
        v   → w        (German w = [v])
    Word-final:
        z   → s        (word-final devoicing in German anyway)
"""

from __future__ import annotations

import re


def respell_for_espeak(text: str) -> str:
    """Convert YIVO romanized Yiddish to German-espeak-friendly spelling.

    Operates on romanized Latin text (output of yiddish.transliterate()).
    Processes word-by-word to handle position-sensitive rules (word-initial,
    word-final).

    Args:
        text: YIVO romanized Yiddish (e.g. "vi geyt es")

    Returns:
        Respelled text (e.g. "wi gejt es")
    """
    # Split on whitespace, preserving punctuation attached to words
    tokens = re.findall(r"[^\s]+|\s+", text)
    result = []
    for token in tokens:
        if token.isspace():
            result.append(token)
        else:
            result.append(_respell_word(token))
    return "".join(result)


def _respell_word(word: str) -> str:
    """Respell a single word (may include trailing punctuation)."""
    # Separate trailing punctuation
    match = re.match(r"^(.*?)([.!?,;:\"')\]]+)?$", word)
    if not match:
        return word
    core = match.group(1)
    punct = match.group(2) or ""

    if not core:
        return word

    # Apply transforms in order (longer patterns first to avoid conflicts)
    out = core

    # Multi-char consonant clusters (order matters — longest first)
    out = out.replace("tsh", "tsch")

    # sh → sch, but word-initial sht → st, shp → sp (German rule)
    out = _replace_sh(out)

    # zh → j (German "j" in loanword context ≈ ʒ; "journal" works)
    out = out.replace("zh", "j")

    # kh → ch
    out = out.replace("kh", "ch")

    # ts → z (German z = [ts]) — must come after tsch replacement
    out = out.replace("ts", "z")

    # Diphthongs: ey→ej, ay→aj, oy→oj
    out = out.replace("ey", "ej")
    out = out.replace("ay", "aj")
    out = out.replace("oy", "oj")

    # z → s (German s before vowel = [z], which is what Yiddish z is)
    # Must come after ts→z and zh→j to avoid double-replacing
    out = _replace_z(out)

    # v → w at word start (German w = [v])
    if out.startswith("v"):
        out = "w" + out[1:]

    return out + punct


def _replace_sh(word: str) -> str:
    """Replace sh→sch, but handle word-initial sht→st and shp→sp.

    In German, word-initial "st" and "sp" are pronounced [ʃt] and [ʃp],
    so we don't need the "sch" prefix for those.
    """
    if word.startswith("sht"):
        word = "st" + word[3:]
    elif word.startswith("shp"):
        word = "sp" + word[3:]

    # Replace remaining "sh" with "sch"
    word = word.replace("sh", "sch")
    return word


def _replace_kh(word: str) -> str:
    """Replace kh→ch, but only after a vowel.

    German word-initial "ch" before a/o/u is pronounced [ʃ] (French loanword
    rule: "Chance", "Charme"). After a vowel, "ch" correctly gives [x] (ach-Laut)
    or [ç] (ich-Laut). At word start, we leave "kh" as-is — espeak produces
    aspirated [kʰ] which is closer to [x] than [ʃ] is.
    """
    if "kh" not in word:
        return word

    result = []
    i = 0
    while i < len(word):
        if word[i:i+2] == "kh":
            # Check if preceded by a vowel
            if i > 0 and result and result[-1] in "aeiou":
                result.append("ch")
            else:
                result.append("kh")
            i += 2
        else:
            result.append(word[i])
            i += 1
    return "".join(result)


def _replace_z(word: str) -> str:
    """Replace z→s for the voiced [z] sound.

    German "s" before a vowel is voiced [z], which matches Yiddish "z".
    We only replace standalone "z" (not part of "tz", "sch", "tsch", "zz").
    At this point ts→z and zh→j have already been applied, so any remaining
    "z" is a Yiddish voiced z.
    """
    # After the ts→z transform, the German "z" chars represent [ts] which is
    # correct. We need to turn remaining YIVO "z" (voiced) into "s".
    # But ts→z already ran, so we can't distinguish. Instead, let's be smarter:
    # we re-approach this differently.
    #
    # Actually, at this point all original "ts" are now "z" (German [ts]) — correct.
    # And all original "z" are still "z" — but should become "s" for German [z].
    # We can't distinguish them anymore.
    #
    # Solution: we need to handle z→s BEFORE ts→z. Let me restructure.
    return word


# The ordering problem above means we need a different approach for z/ts.
# Let's use a marker-based approach.

def _respell_word(word: str) -> str:  # noqa: F811 — intentional redefinition
    """Respell a single word (may include trailing punctuation)."""
    match = re.match(r"^(.*?)([.!?,;:\"')\]]+)?$", word)
    if not match:
        return word
    core = match.group(1)
    punct = match.group(2) or ""

    if not core:
        return word

    out = core

    # Step 1: Protect multi-char sequences with markers
    # tsh → MARKER_TSH (must come before sh and ts replacements)
    out = out.replace("tsh", "\x01")
    # ts → MARKER_TS (must come before z replacement)
    out = out.replace("ts", "\x02")
    # sh → handled specially (sht/shp at start)
    out = _replace_sh(out)  # sh→sch (or st/sp at word start)
    # zh → j
    out = out.replace("zh", "j")
    # kh → ch, but NOT at word start (German word-initial "ch" before a/o/u = [ʃ])
    out = _replace_kh(out)

    # Step 2: Now z is only YIVO voiced-z. Replace z→s.
    out = out.replace("z", "s")

    # Step 3: Restore markers
    out = out.replace("\x01", "tsch")  # tsh → tsch
    out = out.replace("\x02", "z")     # ts → z (German z = [ts])

    # Step 4: Diphthongs
    out = out.replace("ey", "ej")
    out = out.replace("ay", "aj")
    out = out.replace("oy", "oj")

    # Step 5: v → w everywhere (German w = [v])
    out = out.replace("v", "w")

    return out + punct
