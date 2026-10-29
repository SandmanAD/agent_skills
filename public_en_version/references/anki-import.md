# Anki import and templates

Official guide: https://docs.ankiweb.net/importing/text-files.html
For disputed settings check the current documentation. Do not confuse the note type with the deck name: they are different settings.

Below, `<Language>` is the name of the first field (German, French, Czech…) and `<Translation>` is the name of the translation language the user chose (English, Russian, Spanish…), as in the CSV. Put the real names into the instructions you give the user.

## New note type

Tools → Manage Note Types → Add → Clone: Basic (and reversed card). Name the type after the language pair (e.g. "German–English").
In Fields rename Front to `<Language>`, Back to `<Translation>`;
add `<Language> Example`, `<Translation> Example`, Transcription in that order.
Two cards per note: `<Language>` → `<Translation>` and `<Translation>` → `<Language>`. If the user
wants only one direction, clone plain Basic. With two directions, recommend turning on
Burying (new, review and interday learning siblings) in the deck options, so both cards
of a word do not come up on the same day.
A separate type for each language pair: changing one deck's template does not affect the others.
For an existing type add only the missing fields.

## Card design

The ready design is in `assets/design/`: `front.html`, `back.html` (first template),
`reverse_front.html`, `reverse_back.html` (second template, the reverse card) and `card.css`.

- Front: direction label ("DE → EN"), word, IPA. The example is not shown on the front.
- Back: translation and the example block — example and its translation (audio button only with `--tts`).
- Reverse card: translation and the translated example as context; on the back — word, IPA, example.
- Light and dark theme, a separate phone layout (up to 480px).
- An extended note in the translation field (`<br><br><small>…</small>`, only in decks with HTML)
  is shown as small grey text and hidden on the reverse-card question, because it often gives the answer away.

**If AnkiConnect is installed** (add-on `2055492159`, Anki open) — apply it yourself:

```sh
python3 scripts/apply_design.py --model 'German–English' --language-field German --code DE \
  --translation-field English --translation-code EN
```

`--tts` — if the user wants audio: the Anki built-in TTS language for the example
(it_IT, de_DE, fr_FR, es_ES, cs_CZ, pl_PL, en_US…); without the option there is no button. On iPhone Siri voices
are not available to third-party apps; the best option is a Premium/Enhanced voice selected in
Settings → Accessibility → VoiceOver → Speech → Rotor Languages. By default Anki plays the audio itself when the back is shown;
this is turned off in the deck options: Audio → Don't play audio automatically.
`--example-transcription-field` — only if the user agreed to example IPA (see SKILL.md).

The script first saves the current templates and CSS to `backups/`, then changes only
the templates and styling: fields, notes and review history are not touched. Undo —
`--restore <backup file>`. Do not delete card templates: their cards and progress
are deleted with them. After applying, check the look via `cardsInfo` (HTML rendered by Anki;
audio shows up there as `[anki:play:…]`) and tell the user to sync Anki
so the design reaches their phone.

**Without AnkiConnect** — give the user the file contents with the placeholders replaced:
`%WORD%` → `<Language>`, `%WORD_EX%` → `<Language> Example`, `%TRANSLATION%` → `<Translation>`,
`%TRANSLATION_EX%` → `<Translation> Example`, `%IPA%` → Transcription, `%DIR%` → "DE → EN",
`%RDIR%` → "EN → DE", `%TTS%` → ` {{tts de_DE:German Example}}` or empty,
`%EXAMPLE_IPA%` → empty (or the example IPA field block, if it exists). Paste into: Cards → Front/Back Template of each template, and Styling.

Names in `{{…}}` must match the field names exactly, including case and spaces.
An empty field does not create an empty block. Styling comes from the template, not the CSV.
A template applies to all notes of that type; if the type is also used for another
group that needs its own look, clone the type first and apply it to the relevant notes.

## Import

File → Import, choose the CSV. The separator (Comma) and HTML (off) are set by the file's header lines — check that Anki picked them up.
Choose the created type and the target deck. Map fields by name:

1. `<Language>`
2. `<Translation>`
3. `<Language> Example`
4. `<Translation> Example`
5. Transcription
6. Tags → Tags if the file was created with `--tags`; otherwise Tags → (Nothing).

`#` header lines are not imported as cards; no need to skip the first row.
On a first import, N new notes give N cards only with a single card template.
Tags like `level::B1` form a hierarchy in the Anki browser: you can filter by them
or build a filtered deck (e.g. `tag:level::B2`).

## Updating existing cards

Do not delete old cards. Use the same existing note type and an unchanged
first column. Before enriching the CSV, keep the old four fields character for character if
the user only asked to add IPA. Do not fix even the punctuation of the first field.

First add the Transcription field to the existing type, then import the new CSV.
Existing notes → Update. Choose the deck with the old notes; if available,
Match scope → Note Type and Deck limits matching to the chosen deck.
Match scope → Note Type looks for matches in all decks of that type.

Updating matched notes keeps the review schedule. If all N notes
were imported and their first fields did not change, expect N updates and no new
notes. See the actual result in Anki's report. Do not promise no duplicates
if the note type or keys differ, or the original notes already contain duplicates.
