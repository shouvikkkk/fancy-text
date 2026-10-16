#!/usr/bin/env python3
"""fancy-text: convert plain text into 20+ stylish Unicode fonts.

Works as a CLI and as a library::

    $ python fancy_text.py "hello" --style bold
    $ python fancy_text.py "hello" --list
    $ python fancy_text.py "hello"          # prints every style

    >>> from fancy_text import stylize
    >>> stylize("hello", "bold")

Characters with no mapping in a style (e.g. digits in the italic block,
punctuation, symbols) are left unchanged.
"""

import argparse
import sys

__all__ = ["stylize", "STYLES", "style_names"]

_ASCII_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ASCII_LOWER = "abcdefghijklmnopqrstuvwxyz"
_ASCII_DIGITS = "0123456789"


def _offset_map(src, base):
    """Map each char of src to a contiguous Unicode block starting at base."""
    return {c: chr(base + i) for i, c in enumerate(src)}


def _math_style(caps_base, lower_base, digit_base=None,
                caps_exc=None, lower_exc=None):
    """Build a mapping from the Mathematical Alphanumeric Symbols block.

    A few positions in the script / fraktur / double-struck ranges are
    unassigned in Unicode; the real characters live at compatibility
    code points instead (e.g. script B is U+212C, not U+1D49D).
    Those are patched in via caps_exc / lower_exc.
    """
    m = _offset_map(_ASCII_UPPER, caps_base)
    m.update(_offset_map(_ASCII_LOWER, lower_base))
    if digit_base is not None:
        m.update(_offset_map(_ASCII_DIGITS, digit_base))
    for k, v in (caps_exc or {}).items():
        m[k] = v
    for k, v in (lower_exc or {}).items():
        m[k] = v
    return m


# --- compatibility exceptions in the math alphanumeric blocks ---
_SCRIPT_CAPS_EXC = {
    "B": "\u212C",  # ℬ  SCRIPT CAPITAL B
    "E": "\u2130",  # ℰ  SCRIPT CAPITAL E
    "F": "\u2131",  # ℱ  SCRIPT CAPITAL F
    "H": "\u210B",  # ℋ  SCRIPT CAPITAL H
    "I": "\u2110",  # ℐ  SCRIPT CAPITAL I
    "L": "\u2112",  # ℒ  SCRIPT CAPITAL L
    "M": "\u2133",  # ℳ  SCRIPT CAPITAL M
    "R": "\u211B",  # ℛ  SCRIPT CAPITAL R
}
_FRAKTUR_CAPS_EXC = {
    "C": "\u212D",  # ℭ  BLACK-LETTER CAPITAL C
    "H": "\u210C",  # ℌ  BLACK-LETTER CAPITAL H
    "I": "\u2111",  # ℑ  BLACK-LETTER CAPITAL I
    "R": "\u211C",  # ℜ  BLACK-LETTER CAPITAL R
    "Z": "\u2128",  # ℨ  BLACK-LETTER CAPITAL Z
}
_DOUBLESTRUCK_CAPS_EXC = {
    "C": "\u2102",  # ℂ  DOUBLE-STRUCK CAPITAL C
    "H": "\u210D",  # ℍ  DOUBLE-STRUCK CAPITAL H
    "N": "\u2115",  # ℕ  DOUBLE-STRUCK CAPITAL N
    "P": "\u2119",  # ℙ  DOUBLE-STRUCK CAPITAL P
    "Q": "\u211A",  # ℚ  DOUBLE-STRUCK CAPITAL Q
    "R": "\u211D",  # ℝ  DOUBLE-STRUCK CAPITAL R
    "Z": "\u2124",  # ℤ  DOUBLE-STRUCK CAPITAL Z
}


def _circled_digits():
    m = {"0": "\u24EA"}  # ⓪
    m.update(_offset_map("123456789", 0x2460))  # ①–⑨
    return m


def _circled():
    m = _offset_map(_ASCII_UPPER, 0x24B6)   # Ⓐ–Ⓩ
    m.update(_offset_map(_ASCII_LOWER, 0x24D0))  # ⓐ–ⓩ
    m.update(_circled_digits())
    return m


def _squared():
    # Squared caps exist (🄰–🄿); squared lowercase does not, so lowercase
    # uses the parenthesized block (⒜–⒵) and digits use circled (⓪①–⑨).
    m = _offset_map(_ASCII_UPPER, 0x1F130)   # 🄰–🄿
    m.update(_offset_map(_ASCII_LOWER, 0x249C))  # ⒜–⒵
    m.update(_circled_digits())
    return m


def _fullwidth():
    return {c: chr(ord(c) + 0xFEE0)
            for c in _ASCII_UPPER + _ASCII_LOWER + _ASCII_DIGITS}


def _regional_indicator():
    # Regional indicator symbols are caseless; both cases map to the same.
    m = _offset_map(_ASCII_UPPER, 0x1F1E6)  # 🇦–🇿
    m.update({c: m[c.upper()] for c in _ASCII_LOWER})
    return m


def _small_caps():
    # No contiguous block exists; hand-built from real small-cap code points.
    # q and x have no small-cap forms in Unicode -> plain capitals used.
    table = {
        "a": "\u1D00", "b": "\u0299", "c": "\u1D04", "d": "\u1D05",
        "e": "\u1D07", "f": "\uA730", "g": "\u0262", "h": "\u029C",
        "i": "\u026A", "j": "\u1D0A", "k": "\u1D0B", "l": "\u029F",
        "m": "\u1D0D", "n": "\u0274", "o": "\u1D0F", "p": "\u1D18",
        "q": "Q",     "r": "\u0280", "s": "\uA731", "t": "\u1D1B",
        "u": "\u1D1C", "v": "\u1D20", "w": "\u1D21", "x": "X",
        "y": "\u028F", "z": "\u1D22",
    }
    m = dict(table)
    m.update({c.upper(): v for c, v in table.items()})  # caseless style
    return m


def _upside_down():
    table = {
        "a": "\u0250", "b": "q",      "c": "\u0254", "d": "p",
        "e": "\u01DD", "f": "\u025F", "g": "\u0183", "h": "\u0265",
        "i": "\u1D09", "j": "\u027E", "k": "\u029E", "l": "l",
        "m": "\u0270", "n": "u",      "o": "o",      "p": "d",
        "q": "b",      "r": "\u0279", "s": "s",      "t": "\u0287",
        "u": "n",      "v": "\u028C", "w": "\u028D", "x": "x",
        "y": "\u028E", "z": "z",
        # A and E have dedicated reversed capitals; the rest reuse the
        # lowercase flips (standard for upside-down text converters).
        "A": "\u2C6F", "E": "\u018E",
    }
    m = dict(table)
    for c in _ASCII_UPPER:
        if c not in m:
            m[c] = table[c.lower()]
    # Only digits with unambiguous flipped forms are mapped.
    m.update({"0": "0", "1": "\u0196", "2": "\u1105", "3": "\u0190",
              "6": "9", "8": "8", "9": "6"})
    return m


def _combining(comb):
    # Strikethrough / underline: append a combining mark to each char.
    # Spaces are left alone so word gaps stay clean.
    return {c: c + comb for c in _ASCII_UPPER + _ASCII_LOWER + _ASCII_DIGITS}


_BOLD = _math_style(0x1D400, 0x1D41A, digit_base=0x1D7CE)
_ITALIC = _math_style(0x1D434, 0x1D44E)
_BOLD_ITALIC = _math_style(0x1D468, 0x1D482)
_SCRIPT = _math_style(0x1D49C, 0x1D4B6, caps_exc=_SCRIPT_CAPS_EXC)
_BOLD_SCRIPT = _math_style(0x1D4D0, 0x1D4EA)
_FRAKTUR = _math_style(0x1D504, 0x1D51E, caps_exc=_FRAKTUR_CAPS_EXC)
_BOLD_FRAKTUR = _math_style(0x1D56C, 0x1D586)
_DOUBLE_STRUCK = _math_style(0x1D538, 0x1D552, digit_base=0x1D7D8,
                             caps_exc=_DOUBLESTRUCK_CAPS_EXC)
_SANS = _math_style(0x1D5A0, 0x1D5BA, digit_base=0x1D7E2)
_SANS_BOLD = _math_style(0x1D5D4, 0x1D5EE, digit_base=0x1D7EC)
_SANS_ITALIC = _math_style(0x1D608, 0x1D622)
_SANS_BOLD_ITALIC = _math_style(0x1D63C, 0x1D656)
_MONOSPACE = _math_style(0x1D670, 0x1D68A, digit_base=0x1D7F6)
_FULLWIDTH = _fullwidth()


def _apply(mapping, text):
    return "".join(mapping.get(c, c) for c in text)


def _vaporwave(text):
    # Fullwidth + a space between every character (word gaps widen).
    return " ".join(_FULLWIDTH.get(c, c) for c in text)


STYLES = {
    "bold": lambda t: _apply(_BOLD, t),
    "italic": lambda t: _apply(_ITALIC, t),
    "bold_italic": lambda t: _apply(_BOLD_ITALIC, t),
    "monospace": lambda t: _apply(_MONOSPACE, t),
    "script": lambda t: _apply(_SCRIPT, t),
    "bold_script": lambda t: _apply(_BOLD_SCRIPT, t),
    "fraktur": lambda t: _apply(_FRAKTUR, t),
    "bold_fraktur": lambda t: _apply(_BOLD_FRAKTUR, t),
    "double_struck": lambda t: _apply(_DOUBLE_STRUCK, t),
    "sans": lambda t: _apply(_SANS, t),
    "sans_bold": lambda t: _apply(_SANS_BOLD, t),
    "sans_italic": lambda t: _apply(_SANS_ITALIC, t),
    "sans_bold_italic": lambda t: _apply(_SANS_BOLD_ITALIC, t),
    "circled": lambda t: _apply(_circled(), t),
    "squared": lambda t: _apply(_squared(), t),
    "fullwidth": lambda t: _apply(_FULLWIDTH, t),
    "vaporwave": _vaporwave,
    "small_caps": lambda t: _apply(_small_caps(), t),
    "upside_down": lambda t: _apply(_upside_down(), t),
    "strikethrough": lambda t: _apply(_combining("\u0336"), t),
    "underline": lambda t: _apply(_combining("\u0332"), t),
    "regional_indicator": lambda t: _apply(_regional_indicator(), t),
}

# Style one-liners for --help / README.
DESCRIPTIONS = {
    "bold": "Mathematical bold (𝐀𝐁𝐂)",
    "italic": "Mathematical italic (𝐴𝐵𝐶)",
    "bold_italic": "Mathematical bold italic (𝑨𝑩𝑪)",
    "monospace": "Mathematical monospace (𝙰𝙱𝙲)",
    "script": "Mathematical script (𝒜ℬ𝒞)",
    "bold_script": "Mathematical bold script (𝓐𝓑𝓒)",
    "fraktur": "Blackletter / fraktur (𝔄ℭ𝔇)",
    "bold_fraktur": "Bold blackletter (𝕬𝕭𝕮)",
    "double_struck": "Double-struck / blackboard bold (𝔸ℂ𝔻)",
    "sans": "Sans-serif (𝖠𝖡𝖢)",
    "sans_bold": "Sans-serif bold (𝗔𝗕𝗖)",
    "sans_italic": "Sans-serif italic (𝘈𝘉𝘊)",
    "sans_bold_italic": "Sans-serif bold italic (𝘼𝘽𝘾)",
    "circled": "Circled letters and numbers (Ⓐⓑ①)",
    "squared": "Squared caps + parenthesized lowercase (🄰⒜①)",
    "fullwidth": "Fullwidth / ａｅｓｔｈｅｔｉｃ",
    "vaporwave": "Fullwidth with wide spacing (ｖａｐｏｒｗａｖｅ)",
    "small_caps": "Small capitals (ᴀʙᴄ)",
    "upside_down": "Flipped upside down (ɐqɔ)",
    "strikethrough": "S̶t̶r̶i̶k̶e̶t̶h̶r̶o̶u̶g̶h̶",
    "underline": "U̲n̲d̲e̲r̲l̲i̲n̲e̲",
    "regional_indicator": "Regional indicator letters (🇦🇧🇨)",
}


def style_names():
    """Return the available style names in display order."""
    return list(STYLES)


def stylize(text, style):
    """Convert *text* to the given *style*. Raises ValueError if unknown."""
    try:
        fn = STYLES[style]
    except KeyError:
        raise ValueError(
            "unknown style %r; choose from: %s" % (style, ", ".join(STYLES))
        ) from None
    return fn(text)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="fancy_text",
        description="Convert plain text into stylish Unicode fonts "
                    "for social bios and posts.",
    )
    parser.add_argument("text", nargs="?",
                        help="text to style (reads stdin if omitted)")
    parser.add_argument("-s", "--style", metavar="NAME",
                        help="style name (default: print every style)")
    parser.add_argument("-l", "--list", action="store_true",
                        help="list all style names and exit")
    args = parser.parse_args(argv)

    if args.list:
        print("\n".join(style_names()))
        return 0

    if args.style is not None and args.style not in STYLES:
        print("error: unknown style %r" % args.style, file=sys.stderr)
        print("available styles: " + ", ".join(style_names()), file=sys.stderr)
        return 1

    if args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read().rstrip("\n")

    if args.style is not None:
        print(stylize(text, args.style))
    else:
        for name in style_names():
            print("%s: %s" % (name, stylize(text, name)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
