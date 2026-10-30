#!/usr/bin/env python3
"""Terminal rocket. Run: python3 launch.py. Quit: Q, Esc or Ctrl+C.
Python 3 standard library only; macOS/Linux. No network or shell changes.
"""
import curses
import math
import random
import sys
import time


def animate(screen):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    screen.nodelay(True)
    colors = curses.has_colors()
    if colors:
        curses.start_color()
        for i, color in enumerate((curses.COLOR_WHITE, curses.COLOR_RED,
                                   curses.COLOR_CYAN, curses.COLOR_YELLOW), 1):
            curses.init_pair(i, color, curses.COLOR_BLACK)

    def put(y, x, text, color=1):
        height, width = screen.getmaxyx()
        if 0 <= y < height and 0 <= x < width - 1:
            try:
                screen.addstr(y, x, text[:width - x - 1],
                              curses.color_pair(color) if colors else 0)
            except curses.error:
                pass

    start = time.monotonic()
    while True:
        t = time.monotonic() - start
        if t > 10 or screen.getch() in (ord('q'), ord('Q'), 27):
            break
        height, width = screen.getmaxyx()
        screen.erase()
        if height < 12 or width < 30:
            put(0, 0, 'Enlarge terminal. Q to quit.')
            screen.refresh()
            time.sleep(0.04)
            continue
        # Rocket is scaled to the live terminal size, including on resize.
        body_h = max(8, int(height * 0.7))
        radius = max(3, min(width // 9, body_h // 3))
        center = width // 2
        progress = min(1.0, max(0.0, (t - 2.7) / 3.0))
        top = round(height - progress * (height - 3))
        if t > 7:
            top -= round(((t - 7) / 2.0) ** 2 * (height + body_h))
        # Deterministic stars, with occasional twinkling.
        for n in range(35):
            x = (n * 31 + 7) % (width - 1)
            y = (n * 13 + 5) % max(1, height - 3)
            if (n + int(t * 2)) % 5:
                put(y, x, '.', 3)
        # Rolling exhaust before and during the reveal.
        smoke_h = min(height // 3, 2 + int(t * 1.7))
        if t < 7.5:
            for y in range(height - smoke_h, height - 1):
                for x in range(1, width - 1):
                    wave = math.sin(x * 0.24 + t * 4 + y * 0.8)
                    if wave > 0.05 and random.random() < 0.48:
                        put(y, x, random.choice('~.:oO'), 1)
        if t >= 2.7:
            nose_h = max(3, radius)
            for row in range(body_h):
                y = top + row
                r = min(radius, max(0, round(radius * row / nose_h)))
                for dx in range(-r, r + 1):
                    char, color = ' ', 1
                    if row < nose_h:
                        char, color = '/', 2
                        if dx >= 0:
                            char = '\\'
                        if row == 0:
                            char = '^'
                    elif abs(dx) == radius:
                        char = '|'
                    elif row in (nose_h, body_h - 1):
                        char, color = '=', 2
                    elif abs(row - (nose_h + 3)) <= 1 and abs(dx) <= 2:
                        char, color = 'O', 3
                    put(y, center + dx, char, color)
                if row > body_h * 0.65:
                    fin = max(1, int((row - body_h * 0.65) * 0.8))
                    put(y, center - radius - fin, '/' + '#' * (fin - 1), 2)
                    put(y, center + radius + 1, '#' * (fin - 1) + '\\', 2)
            put(top + nose_h + 6, center - 1, '42', 2)
            for row in range(max(3, height // 4)):
                spread = max(0, radius - row // 2)
                for dx in range(-spread, spread + 1):
                    put(top + body_h + row, center + dx,
                        random.choice('*^:. '), random.choice((2, 4)))
        label = ('IGNITION' if t < 2.7 else 'READY FOR LIFTOFF' if t < 7
                 else 'LIFTOFF!')
        put(0, max(0, (width - len(label)) // 2), label, 4)
        put(height - 1, 1, 'Q / Esc / Ctrl+C to quit', 3)
        screen.refresh()
        time.sleep(1 / 30)


def main():
    if not sys.stdout.isatty() or not sys.stdin.isatty():
        print('Run in an interactive terminal: python3 launch.py', file=sys.stderr)
        return 1
    try:
        curses.wrapper(animate)
    except KeyboardInterrupt:
        pass
    except curses.error as error:
        print('Terminal could not start animation: {}'.format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
