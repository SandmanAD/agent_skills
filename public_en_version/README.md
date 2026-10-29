# anki-language-cards

A skill for AI agents (Claude Code, Codex) that creates Anki language flashcards for any language. The output is a validated UTF-8 CSV with a translation, an example sentence, the example's translation and IPA, ready to import. The card design can be applied directly in Anki via AnkiConnect.

## Features

- **Any language.** Rules for English, German, French, Spanish, Italian, Portuguese, Czech and Polish, plus general rules for the rest: articles, gender, verb forms, pronunciation norm, dictionaries for checking.
- **Four scenarios:**
  - cards from your own word list;
  - picking N words for a topic and level;
  - words from a song, text or subtitles;
  - updating an existing deck, e.g. adding IPA, without duplicates.
- **No level bias in word selection.** Words of any difficulty are treated equally; only obsolete and rare words are excluded. The CEFR level is added as a tag, not used as a filter.
- **File validation.** The script checks the note count, empty fields, duplicates, IPA format and lossless CSV read-back.
- **Any translation language.** The agent asks which language to translate into (usually your native one) before making cards.
- **Ready design.** Light and dark theme, phone layout, two cards per word: target language → translation and back.

## Card format

| Field | Example |
|---|---|
| `German` | das Essen |
| `English` | food |
| `German Example` | Das Essen ist fertig. |
| `English Example` | The food is ready. |
| `Transcription` | /das ˈɛsn̩/ |

The fields are named after the target language and the translation language (German → English here). There is no default translation language: the agent asks for it. Optional fields: `Tags` (level, topic, source) and example IPA (on request, for languages with unpredictable pronunciation).

## Installation

Copy the folder into your agent's skills directory. The folder must have the same name as the skill:

```bash
cp -R anki-language-cards/en ~/.claude/skills/anki-language-cards
```

For Codex, the interface description is in `agents/openai.yaml`.

**Requirements**

- Python 3.8+, no external dependencies.
- Anki 2.1.55+ (CSV import with header lines).
- Optional: [AnkiConnect](https://ankiweb.net/shared/info/2055492159) — needed to apply the design directly in Anki.

## Usage

Just ask the agent:

- "Create 80 German A2 cards for travel, translations into English"
- "Turn the words from this French song into cards" — the agent will ask for the translation language
- "Make cards from these English words with Spanish translations, British IPA: …"
- "Add IPA to this CSV, keep the four old fields"
- "Apply the design to my German–English note type"

The agent returns a CSV and short import instructions. On the first import for a language, card templates are included as well.

## Scripts

The agent runs them itself. You only need them manually for debugging.

```bash
# JSON with cards → validated CSV for Anki
python3 scripts/export_anki.py cards.json German.csv --language-field German --translation-field English --expected 100 --tags

# Apply the design to a note type (templates are backed up to backups/ first)
python3 scripts/apply_design.py --model 'German–English' --language-field German --code DE --translation-field English --translation-code EN

# Roll back the design
python3 scripts/apply_design.py --model 'German–English' --restore backups/<file>.json
```

All options are in each script's `--help`.

## Structure

```
SKILL.md                  instructions for the agent
agents/openai.yaml        Codex interface
assets/design/            card templates and CSS
references/languages.md   language specifics
references/anki-import.md import, design, deck updates
scripts/export_anki.py    building and validating the CSV
scripts/apply_design.py   applying the design via AnkiConnect
```

## Limitations

- The scripts check the file structure, not the language. The agent proofreads translations and IPA separately.
- The CSV does not create a note type or templates. Create them once by hand (see `references/anki-import.md`) or apply them via AnkiConnect.
- `apply_design.py` changes only templates and CSS. It does not touch fields, notes or review progress.
