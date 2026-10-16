# fancy-text

Unicode text styler: convert plain text into 22 stylish fonts for social bios and posts.

No dependencies, no install — just Python 3 and the standard library.

## Usage

```bash
# One style
python fancy_text.py "hello" --style bold
# 𝐡𝐞𝐥𝐥𝐨

# List all style names
python fancy_text.py "hello" --list

# Print EVERY style with its name
python fancy_text.py "hello"

# Read from stdin
echo "midnight drive" | python fancy_text.py --style vaporwave
# ｍ ｉ ｄ ｎ ｉ ｇ ｈ ｔ   ｄ ｒ ｉ ｖ ｅ
```

More examples (real output):

```bash
$ python fancy_text.py "Deals Network" --style small_caps
ᴅᴇᴀʟꜱ ɴᴇᴛᴡᴏʀᴋ

$ python fancy_text.py "sale ends tonight" --style strikethrough
s̶a̶l̶e̶ e̶n̶d̶s̶ t̶o̶n̶i̶g̶h̶t̶

$ python fancy_text.py "Hello 123" --style circled
Ⓗⓔⓛⓛⓞ ①②③
```

## Styles

Sample text: `Abc 123`. Styles are built programmatically from Unicode
code-point offsets wherever the blocks are contiguous (the Mathematical
Alphanumeric Symbols block, circled/fullwidth ranges, regional indicators),
with hand-built tables for the rest. Characters with no mapping in a style
(digits in the italic block, punctuation, symbols) are left unchanged.

| Style | Sample |
|---|---|
| `bold` | 𝐀𝐛𝐜 𝟏𝟐𝟑 |
| `italic` | 𝐴𝑏𝑐 123 |
| `bold_italic` | 𝑨𝒃𝒄 123 |
| `monospace` | 𝙰𝚋𝚌 𝟷𝟸𝟹 |
| `script` | 𝒜𝒷𝒸 123 |
| `bold_script` | 𝓐𝓫𝓬 123 |
| `fraktur` | 𝔄𝔟𝔠 123 |
| `bold_fraktur` | 𝕬𝖇𝖈 123 |
| `double_struck` | 𝔸𝕓𝕔 𝟙𝟚𝟛 |
| `sans` | 𝖠𝖻𝖼 𝟣𝟤𝟥 |
| `sans_bold` | 𝗔𝗯𝗰 𝟭𝟮𝟯 |
| `sans_italic` | 𝘈𝘣𝘤 123 |
| `sans_bold_italic` | 𝘼𝙗𝙘 123 |
| `circled` | Ⓐⓑⓒ ①②③ |
| `squared` | 🄰⒝⒞ ①②③ |
| `fullwidth` | Ａｂｃ １２３ |
| `vaporwave` | Ａ ｂ ｃ   １ ２ ３ |
| `small_caps` | ᴀʙᴄ 123 |
| `upside_down` | Ɐqɔ ƖᄅƐ |
| `strikethrough` | A̶b̶c̶ 1̶2̶3̶ |
| `underline` | A̲b̲c̲ 1̲2̲3̲ |
| `regional_indicator` | 🇦🇧🇨 123 |

Notes:

- **script / fraktur / double-struck** use Unicode's compatibility code points
  for the handful of letters whose slots are unassigned in the contiguous
  block (e.g. script `B` → `ℬ` U+212C, double-struck `R` → `ℝ` U+211D).
- **squared** mixes blocks: squared capitals (🄰–🄿), parenthesized lowercase
  (⒜–⒵) and circled digits (⓪①–⑨), since squared lowercase doesn't exist
  in Unicode.
- **regional_indicator** letters may render as flag emoji on some platforms
  when two appear side by side — that's how the platform displays them.

## Library usage

```python
from fancy_text import stylize, style_names

stylize("hello", "bold")      # '𝐡𝐞𝐥𝐥𝐨'
stylize("hello", "vaporwave") # 'ｈ ｅ ｌ ｌ ｏ'
style_names()                 # ['bold', 'italic', ...]  (22 styles)

stylize("hello", "nope")      # raises ValueError with the valid style list
```

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Shouvik Maji.
