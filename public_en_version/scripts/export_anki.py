#!/usr/bin/env python3
"""Export reviewed five-field JSON notes as an Anki-compatible UTF-8 CSV."""
import argparse
import csv
import io
import json
from pathlib import Path
import re
import unicodedata

CYRILLIC = re.compile('[Ѐ-ӿ]')


def key(value):
    value = unicodedata.normalize('NFC', value).casefold()
    for char in ('’', '‘', 'ʼ'):
        value = value.replace(char, "'")
    return ' '.join(value.split()).strip().rstrip('?!.,;:')


def read_anki(path):
    text = Path(path).read_text(encoding='utf-8-sig')
    # Only strip the leading Anki metadata block, never lines inside quoted fields.
    lines = text.splitlines(keepends=True)
    while lines and lines[0].startswith('#'):
        lines.pop(0)
    return list(csv.reader(io.StringIO(''.join(lines), newline=''), strict=True))


def field_names(args):
    if args.fields:
        fields = [f.strip() for f in args.fields.split(',')]
        if len(fields) != 5:
            raise ValueError('--fields must list exactly five comma-separated names')
    else:
        if not (args.language_field and args.translation_field):
            raise ValueError('Pass --language-field and --translation-field, or --fields')
        fields = [args.language_field, args.translation_field,
                  args.example_field or args.language_field + ' Example',
                  args.translation_example_field or args.translation_field + ' Example',
                  args.transcription_field]
    if len(set(fields)) != 5 or any(not f for f in fields):
        raise ValueError('Field names must be nonempty and distinct')
    if any(any(c in f for c in ',\r\n') for f in fields):
        raise ValueError('Field names must not contain commas or newlines')
    return fields


def export(args):
    fields = field_names(args)
    extra = [args.example_transcription_field] if args.example_transcription_field else []
    if any(f in fields for f in extra) or any(any(c in f for c in ',\r\n') for f in extra):
        raise ValueError('Invalid or duplicate --example-transcription-field')
    keys = fields + extra + (['Tags'] if args.tags else [])
    notes = json.loads(Path(args.input).read_text(encoding='utf-8'))
    if not isinstance(notes, list) or args.expected < 1 or len(notes) != args.expected:
        raise ValueError(f'Expected exactly {args.expected} notes in a JSON array')
    rows = []
    seen = set()
    for i, note in enumerate(notes, 1):
        if not isinstance(note, dict) or set(note) != set(keys):
            raise ValueError(f'Note {i}: expected exactly these keys: {keys}')
        row = [note[f] for f in keys]
        if any(not isinstance(c, str) for c in row):
            raise ValueError(f'Note {i}: every value must be a string')
        if any(not c.strip() for c in row[:5]):
            raise ValueError(f'Note {i}: all five fields must be nonempty')
        if any('\x00' in c for c in row):
            raise ValueError(f'Note {i}: NUL character is not allowed')
        normalized = key(row[0])
        if not normalized or normalized in seen:
            raise ValueError(f'Note {i}: duplicate or invalid first field: {row[0]!r}')
        seen.add(normalized)
        if key(row[2]) == normalized or key(row[3]) == key(row[1]):
            raise ValueError(f'Note {i}: example must be a sentence, not a copy of the word/translation')
        transcription = row[4]
        if '\n' in transcription or '\r' in transcription:
            raise ValueError(f'Note {i}: {fields[4]} must be a single line')
        if args.transcription_format == 'ipa':
            if not (transcription == transcription.strip() and len(transcription) > 2
                    and transcription.startswith('/') and transcription.endswith('/')):
                raise ValueError(f'Note {i}: {fields[4]} must be a /IPA/ string')
            if CYRILLIC.search(transcription):
                raise ValueError(f'Note {i}: Cyrillic letters in IPA: {transcription!r}')
            if extra and not (row[5].startswith('/') and row[5].endswith('/') and len(row[5]) > 2
                              and not CYRILLIC.search(row[5])):
                raise ValueError(f'Note {i}: {extra[0]} must be a /IPA/ string')
        if args.tags:
            row[-1] = ' '.join(row[-1].split())
        rows.append(row)
    if args.required:
        required = json.loads(Path(args.required).read_text(encoding='utf-8'))
        if not isinstance(required, list) or any(not isinstance(s, str) for s in required):
            raise ValueError('--required must contain a JSON array of strings')
        missing = [s for s in required if key(s) not in seen]
        if missing:
            raise ValueError(f'Missing required entries: {missing}')
    if args.baseline:
        baseline = read_anki(args.baseline)
        if len(baseline) != len(rows) or any(len(r) < 4 for r in baseline):
            raise ValueError('Baseline must have the same number of notes with at least four fields')
        if [r[:4] for r in rows] != [r[:4] for r in baseline]:
            raise ValueError('Baseline mismatch: preserve all four original fields and row order')
    headers = [('separator', 'Comma'), ('html', 'false')]
    for name, value in [('deck', args.deck), ('notetype', args.notetype)]:
        if value:
            if '\n' in value or '\r' in value:
                raise ValueError(f'Invalid newline in {name}')
            headers.append((name, value))
    if args.tags:
        headers.append(('tags column', str(len(keys))))
    headers.append(('columns', ','.join(keys)))
    content = io.StringIO(newline='')
    for name, value in headers:
        content.write(f'#{name}:{value}\n')
    writer = csv.writer(content, quoting=csv.QUOTE_ALL, lineterminator='\n')
    writer.writerows(rows)
    # Verify serialized data before committing the deliverable.
    payload = content.getvalue()
    data = payload.splitlines(keepends=True)
    parsed = list(csv.reader(io.StringIO(''.join(data[len(headers):]), newline=''), strict=True))
    if parsed != rows:
        raise ValueError('CSV round-trip failed')
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload.encode('utf-8', errors='strict'))
    if read_anki(output) != rows:
        raise ValueError('Written CSV round-trip failed')
    added = ''.join(f' + {k}' for k in keys[5:])
    print(f'PASS: {len(rows)} unique notes, five nonempty fields{added}, UTF-8, CSV round-trip.')
    print(f'Columns: {", ".join(keys)}')
    print('Language, IPA accuracy, and actual Anki import require separate review.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', help='JSON array with five named fields per object')
    p.add_argument('output', help='Output CSV path')
    p.add_argument('--language-field', help='German, French, Czech, etc.')
    p.add_argument('--translation-field',
                   help='Translation language chosen by the user, e.g. English, Russian, Spanish')
    p.add_argument('--example-field', help='Default: language field + " Example"')
    p.add_argument('--translation-example-field', help='Default: translation field + " Example"')
    p.add_argument('--transcription-field', default='Transcription')
    p.add_argument('--fields', help='Exact five field names in order (existing note type); '
                   'overrides the options above')
    p.add_argument('--transcription-format', choices=('ipa', 'free'), default='ipa',
                   help='ipa: require /.../; free: pinyin, kana or another agreed system')
    p.add_argument('--example-transcription-field',
                   help='Optional sixth field with IPA of the example (off by default)')
    p.add_argument('--tags', action='store_true',
                   help='Each note also has a "Tags" key (space-separated, may be empty)')
    p.add_argument('--expected', required=True, type=int)
    p.add_argument('--deck')
    p.add_argument('--notetype')
    p.add_argument('--required', help='Optional JSON array of required words/phrases')
    p.add_argument('--baseline', help='Original Anki CSV; preserve its first four fields')
    args = p.parse_args()
    try:
        export(args)
    except (ValueError, OSError, csv.Error) as exc:
        p.exit(1, f'ERROR: {exc}\n')


if __name__ == '__main__':
    main()
