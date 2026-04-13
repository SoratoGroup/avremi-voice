# Avremi — Open-Source Yiddish Text-to-Speech Voice

Avremi is the first open-source neural text-to-speech voice for Yiddish. It produces natural-sounding Yiddish speech from any orthography — YIVO standard, Hasidic, undiacriticized, or mixed text.

**Try it live:** [loqal.digital/yiddish-tts](https://loqal.digital/yiddish-tts)

## Try It Now (No Install)

The fastest way to hear Avremi: **[loqal.digital/yiddish-tts](https://loqal.digital/yiddish-tts)** — type any Yiddish text in the browser and press Listen.

## Run It Yourself

Want to run it on your own machine? Here's everything you need.

### Prerequisites

- **Python 3.9+**
- **espeak-ng** — the open-source speech synthesizer ([install guide](https://github.com/espeak-ng/espeak-ng/blob/master/docs/guide.md))
  - macOS: `brew install espeak-ng`
  - Ubuntu/Debian: `sudo apt install espeak-ng`
  - Windows: download from [espeak-ng releases](https://github.com/espeak-ng/espeak-ng/releases)

### Setup (one time)

```bash
# Clone this repo
git clone https://github.com/SoratoGroup/avremi-voice.git
cd avremi-voice

# Install Python dependencies
pip install piper-tts yiddish
```

### Speak Yiddish

Create a file called `speak.py`:

```python
import wave
import yiddish
from espeak_respell import respell_for_espeak
from piper import PiperVoice

voice = PiperVoice.load("avremi.onnx")

def speak(text, filename="output.wav"):
    """Convert Yiddish text to speech."""
    romanized = yiddish.transliterate(text)
    respelled = respell_for_espeak(romanized)
    with wave.open(filename, "wb") as wav:
        voice.synthesize_wav(respelled, wav)
    print(f"Saved to {filename}")

# Try it!
speak("שלום עליכם, ווי גייט עס אײַך?")
speak("מײַן נאָמען איז אַבֿרמי.", "avremi.wav")
speak("ייִדיש איז אַ שפּראַך פֿון טויזנט יאָר.", "thousand.wav")
```

```bash
python speak.py
# → Saved to output.wav
# → Saved to avremi.wav
# → Saved to thousand.wav

# Play it (macOS)
afplay output.wav
```

That's it — three lines of code to go from Yiddish text to audio.

### Why the Preprocessing?

Avremi uses [Piper](https://github.com/rhasspy/piper), which internally uses espeak-ng's **German** phonemizer to convert text to phonemes. But German espeak misreads YIVO Yiddish romanization — for example, it turns "z" into [ts], mangles "sh", and reads "vi" as the Roman numeral VI.

The `espeak_respell.py` file (included in this repo) fixes this by rewriting the romanization into spellings that German espeak interprets correctly. See [Espeak Respelling](#espeak-respelling) below for the complete mapping.

The [`yiddish`](https://pypi.org/project/yiddish/) Python library handles the Hebrew-to-Latin transliteration.

### For Mobile & Embedded

Avremi also works with [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) for iOS, Android, Raspberry Pi, and other embedded platforms. CPU only — no GPU needed. The model is ~63 MB.

## Model Files

| File | Description |
|------|-------------|
| `avremi.onnx` | Piper VITS model (~63 MB) |
| `avremi.onnx.json` | Model configuration (sample rate, phoneme map) |
| `espeak_respell.py` | Romanization → German-espeak-friendly spelling (required) |

## Preprocessing Pipeline

Avremi expects romanized Latin text, not raw Hebrew script. The full pipeline:

```
Raw Yiddish text (any orthography)
  → Normalize orthography (Hasidic/Soviet → YIVO standard)
  → Expand numbers/currencies/times to Yiddish words
  → Respell loshn-koydesh words phonetically
  → Transliterate Hebrew script → Latin (YIVO romanization)
  → Respell for German espeak compatibility
  → Piper (espeak-ng German phonemizer → VITS → audio)
```

### Espeak Respelling

The German espeak phonemizer misinterprets several YIVO romanization patterns. The following transforms must be applied to romanized text before synthesis:

| YIVO | Respelled | Reason |
|------|-----------|--------|
| `ey` | `ej` | German reads "ey" as schwa+ü |
| `ay` | `aj` | German reads "ay" as [ai] |
| `oy` | `oj` | Ensures consistent diphthong |
| `sh` | `sch` | German "sh" is garbled; "sch" = [ʃ] |
| `sht-` | `st-` | Word-initial only — German "st-" = [ʃt] |
| `shp-` | `sp-` | Word-initial only — German "sp-" = [ʃp] |
| `zh` | `j` | German "j" in loanwords ≈ [ʒ] |
| `tsh` | `tsch` | German "tsch" = [tʃ] |
| `kh` | `ch` | **After vowels only.** German "ch" = [x]/[ç]. Word-initial "ch" before a/o/u = [ʃ] in German, so leave as `kh` |
| `ts` | `z` | German "z" = [ts] |
| `z` | `s` | German "s" before vowel = [z] |
| `v` | `w` | German "w" = [v] |

**Order matters.** Protect `tsh` and `ts` with markers before replacing `z→s`, then restore: `tsh→tsch`, `ts→z`.

Reference implementations:
- **Python:** [`espeak_respell.py`](https://github.com/SoratoOSS/avremi-voice/blob/main/espeak_respell.py)
- The same logic is available in Swift and Kotlin in the [Loqal](https://loqal.digital) app source.

### Loshn-Koydesh (Hebrew-Origin Words)

Yiddish contains thousands of Hebrew and Aramaic-origin words whose spelling doesn't reflect their Yiddish pronunciation. These must be respelled phonetically before transliteration:

| Written | Respelled | Romanized | Meaning |
|---------|-----------|-----------|---------|
| שלום | שאָלעם | sholem | peace/hello |
| תּורה | טױרע | toyre | Torah |
| חזן | כאַזן | khazn | cantor |
| ישיבֿה | יעשיװע | yeshive | yeshiva |
| קדיש | קאַדעש | kadesh | kaddish |

The `yiddish` Python library provides `respell_loshn_koydesh()` with 8,000+ entries. For compound phrases written with spaces (e.g., שלום עליכם), try joining adjacent words with maqaf (שלום־עליכם) to match dictionary entries.

## Phoneme Inventory

Yiddish has 30 phonemes: 22 consonants, 5 vowels, and 3 diphthongs.

### Consonants (22)

| YIVO | IPA | X-SAMPA | Example |
|------|-----|---------|---------|
| b | b | b | **b**ukh (book) |
| d | d | d | **d**ort (there) |
| dzh | d͡ʒ | dZ | **dzh**oygn (to jog) |
| f | f | f | **f**ish (fish) |
| g | ɡ | g | **g**ut (good) |
| h | h | h | **h**oyz (house) |
| k | k | k | **k**ind (child) |
| kh | x | x | na**kh**t (night) |
| l | l | l | **l**and (country) |
| m | m | m | **m**ame (mother) |
| n | n | n | **n**omen (name) |
| p | p | p | **p**onem (face) |
| r | ʁ | R | **r**oyt (red) |
| s | s | s | **s**un (sun) |
| sh | ʃ | S | **sh**ul (synagogue) |
| t | t | t | **t**og (day) |
| ts | t͡s | ts | **ts**ayt (time) |
| tsh | t͡ʃ | tS | **tsh**epe (pot) |
| v | v | v | **v**os (what) |
| y | j | j | **y**or (year) |
| z | z | z | **z**ogn (to say) |
| zh | ʒ | Z | **zh**urnal (journal) |

### Vowels (5)

| YIVO | IPA | X-SAMPA | Example |
|------|-----|---------|---------|
| a | a | a | t**a**te (father) |
| e | ɛ | E | b**e**t (bed) |
| i | i | i | m**i**t (with) |
| o | ɔ | O | d**o**rt (there) |
| u | u | u | h**u**nt (dog) |

### Diphthongs (3)

| YIVO | IPA | X-SAMPA | Example |
|------|-----|---------|---------|
| ay | aj | aj | ts**ay**t (time) |
| ey | ɛj | Ej | kl**ey**n (small) |
| oy | ɔj | Oj | h**oy**z (house) |

### Phoneme Override Tags

For fine-grained pronunciation control, wrap X-SAMPA phonemes in override tags:

```
דער חזן האָט געזונגען <ph>k a d E S</ph>
```

Or using the Hebrew-keyboard-friendly variant:

```
דער חזן האָט געזונגען <פ>k a d E S</פ>
```

Overrides bypass all preprocessing and are inserted directly into the phoneme stream. Escape literal tags with a backslash: `\<ph>`.

## About the Training Data

Avremi is trained on the [REYD corpus](https://datashare.ed.ac.uk/handle/10283/4383) — a dataset of studio-quality Yiddish recordings produced at the University of Edinburgh and the University of Regensburg. The dataset contains 4,892 utterances (~475 minutes) from 3 native speakers reading late 19th and early 20th century Yiddish fiction.

Avremi's voice is based on recordings in the **Polish (Poylish) dialect** — the most widely spoken Yiddish dialect before World War II, characteristic of central Poland (Warsaw, Lodz, Krakow).

## About Yiddish

Yiddish is a Germanic language written in Hebrew script, spoken for over a thousand years by Ashkenazi Jews across Central and Eastern Europe. At its peak before World War II, it was the daily language of roughly 11 million people.

The language has three major dialect groups:
- **Litvish** (Lithuanian) — Lithuania, Latvia, Belarus. The basis for YIVO standard orthography.
- **Poylish** (Polish) — Central Poland, Galicia. The most widely spoken dialect pre-war.
- **Galitzianer** (Ukrainian) — Western Ukraine, Romania, Hungary.

Today, Yiddish remains a living first language for hundreds of thousands of Hasidic Jews in Brooklyn, Antwerp, Jerusalem, and Montreal, and is taught at universities worldwide.

## License

- **Model files** (ONNX, config): **CC BY-SA 4.0** — consistent with the REYD corpus license
- **Code** (Python, Swift, Kotlin): **MIT** — use freely in any project

## Attribution

- **REYD** — Yiddish speech corpus (University of Edinburgh / University of Regensburg)
- **Piper** — Neural text-to-speech engine (Rhasspy project)
- **yiddish** — Yiddish transliteration library (Jochanan Stenzel)

## Links

- [Try Avremi live](https://loqal.digital/yiddish-tts)
- [Loqal — AI Language Learning App](https://loqal.digital) (iOS & Android)
- [REYD Corpus](https://datashare.ed.ac.uk/handle/10283/4383)
- [Piper TTS](https://github.com/rhasspy/piper)
- [YIVO Institute](https://www.yivo.org)
