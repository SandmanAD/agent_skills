#!/usr/bin/env python3
"""Educational terminal anatomy diagram. Run: python3 launch.py.
Quit with Q, Esc or Ctrl+C. Python standard library only.
"""
import curses
import locale
import sys
import time


DRAWING = [
    "             .------.",
    "           .'   ||   `.",
    "          /     ||     \\",
    "         /              \\",
    "        (                )",
    "         `---._______.---'",
    "             |       |",
    "             |       |",
    "             |       |",
    "             |       |",
    "             |       |",
    "             |       |",
    "          ___|       |___",
    "        .'               `.",
    "       /         :         \\",
    "      (          :          )",
    "      |          :          |",
    "       \\        / \\        /",
    "        `------'   `------'",
]
LABELS = {
    1: '1  Наружное отверстие уретры',
    3: '2  Головка полового члена',
    5: '3  Венец головки',
    9: '4  Ствол полового члена',
    15: '5  Мошонка',
    16: '6  Срединный шов мошонки',
}
# Each number is placed beside the corresponding external structure.
MARKERS = {1: (19, '1'), 3: (26, '2'), 5: (26, '3'),
           9: (23, '4'), 15: (30, '5'), 16: (19, '6')}


def animate(screen):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    screen.nodelay(True)
    colors = curses.has_colors()
    if colors:
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

    def put(y, x, text, color=1):
        height, width = screen.getmaxyx()
        if 0 <= y < height and 0 <= x < width - 1:
            try:
                screen.addstr(y, x, text[:width - x - 1],
                              curses.color_pair(color) if colors else 0)
            except curses.error:
                pass

    while True:
        if screen.getch() in (ord('q'), ord('Q'), 27):
            break
        height, width = screen.getmaxyx()
        screen.erase()
        if height < 24 or width < 68:
            put(0, 0, 'Enlarge terminal to at least 68 x 24.')
        else:
            left = (width - 66) // 2
            put(0, left, 'НАРУЖНЫЕ МУЖСКИЕ ПОЛОВЫЕ ОРГАНЫ', 2)
            put(1, left, 'Учебная схема; крайняя плоть не показана.')
            for row, line in enumerate(DRAWING):
                put(3 + row, left, line)
                if row in MARKERS:
                    column, number = MARKERS[row]
                    put(3 + row, left + column, number, 2)
                if row in LABELS:
                    put(3 + row, left + 36, LABELS[row], 2)
        screen.refresh()
        time.sleep(0.05)


def main():
    if not sys.stdout.isatty() or not sys.stdin.isatty():
        print('Run in an interactive terminal: python3 launch.py', file=sys.stderr)
        return 1
    locale.setlocale(locale.LC_ALL, '')
    try:
        curses.wrapper(animate)
    except KeyboardInterrupt:
        pass
    except curses.error as error:
        print('Terminal could not show diagram: {}'.format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
