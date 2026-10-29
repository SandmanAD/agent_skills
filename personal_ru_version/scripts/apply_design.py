#!/usr/bin/env python3
"""Apply the card design from assets/design to an Anki note type via AnkiConnect.

Backs up the current templates and CSS first; --restore puts a backup back.
Only templates and CSS change: fields, notes and review history stay intact.
"""
import argparse
import datetime
import json
from pathlib import Path
import urllib.request

DESIGN = Path(__file__).resolve().parent.parent / 'assets' / 'design'


def anki(action, **params):
    body = json.dumps({'action': action, 'version': 6, 'params': params}).encode()
    try:
        reply = json.load(urllib.request.urlopen('http://localhost:8765', body, timeout=15))
    except OSError as exc:
        raise SystemExit(f'ERROR: AnkiConnect is not reachable (is Anki open?): {exc}')
    if reply.get('error'):
        raise SystemExit(f'ERROR: {action}: {reply["error"]}')
    return reply['result']


def backup(model, folder):
    data = {'model': model, 'fields': anki('modelFieldNames', modelName=model),
            'templates': anki('modelTemplates', modelName=model),
            'css': anki('modelStyling', modelName=model)['css']}
    stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    path = Path(folder) / f'{model}_{stamp}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    return path, data


def render(name, tokens):
    text = (DESIGN / name).read_text(encoding='utf-8')
    for token, value in tokens.items():
        text = text.replace(f'%{token}%', value)
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', required=True, help='Note type name, e.g. Italiano')
    p.add_argument('--language-field', help='First field, e.g. Italian')
    p.add_argument('--translation-field', default='Russian')
    p.add_argument('--transcription-field', default='Transcription')
    p.add_argument('--code', help='Short label of the studied language, e.g. IT')
    p.add_argument('--translation-code', default='RU')
    p.add_argument('--tts', help='Anki TTS language for the example, e.g. it_IT, de_DE, fr_FR')
    p.add_argument('--example-transcription-field',
                   help='Optional field with IPA of the example (off by default)')
    p.add_argument('--backup-dir', default='backups')
    p.add_argument('--restore', help='Backup JSON to put back instead of applying the design')
    args = p.parse_args()

    if args.restore:
        data = json.loads(Path(args.restore).read_text(encoding='utf-8'))
        path, _ = backup(args.model, args.backup_dir)
        anki('updateModelTemplates', model={'name': args.model, 'templates': data['templates']})
        anki('updateModelStyling', model={'name': args.model, 'css': data['css']})
        print(f'Restored {args.restore}; previous state saved to {path}')
        return

    if not (args.language_field and args.code):
        p.error('--language-field and --code are required unless --restore is used')
    path, current = backup(args.model, args.backup_dir)
    word = args.language_field
    tokens = {'WORD': word, 'WORD_EX': word + ' Example',
              'TRANSLATION': args.translation_field,
              'TRANSLATION_EX': args.translation_field + ' Example',
              'IPA': args.transcription_field,
              'DIR': f'{args.code} → {args.translation_code}',
              'RDIR': f'{args.translation_code} → {args.code}',
              'TTS': f' {{{{tts {args.tts}:{word} Example}}}}' if args.tts else ''}
    needed = [tokens[k] for k in ('WORD', 'WORD_EX', 'TRANSLATION', 'TRANSLATION_EX', 'IPA')]
    tokens['EXAMPLE_IPA'] = ''
    if args.example_transcription_field:
        f = args.example_transcription_field
        needed.append(f)
        tokens['EXAMPLE_IPA'] = f'{{{{#{f}}}}}<div class="example-ipa">{{{{{f}}}}}</div>{{{{/{f}}}}}'
    missing = [f for f in needed if f not in current['fields']]
    if missing:
        raise SystemExit(f'ERROR: note type {args.model!r} has no fields {missing}')

    names = list(current['templates'])
    templates = {names[0]: {'Front': render('front.html', tokens), 'Back': render('back.html', tokens)}}
    if len(names) > 1:
        # Second template is treated as the reverse card; extra templates are left as is.
        templates[names[1]] = {'Front': render('reverse_front.html', tokens),
                               'Back': render('reverse_back.html', tokens)}
    anki('updateModelTemplates', model={'name': args.model, 'templates': templates})
    anki('updateModelStyling', model={'name': args.model, 'css': (DESIGN / 'card.css').read_text(encoding='utf-8')})
    print(f'Backup: {path}')
    print(f'Updated templates {list(templates)} and CSS of {args.model!r}.')
    print(f'Undo: python3 {__file__} --model {args.model!r} --restore {path}')


if __name__ == '__main__':
    main()
