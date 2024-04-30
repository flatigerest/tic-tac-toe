import curses
import sys
import time
import socket
import json
from requests import get as requestsget
from random import randint
import ipaddress

MAX_Y = None
MAX_X = None
STDSCR = None


class Button:
    sleep_time = 0.1

    def __init__(self, parameter, label, x, y):
        self.parameter = parameter
        self.label = label
        self.x = x
        self.y = y
        self.area = {
            "x": [num for num in range(x + 1, x + len(self.label))],
            "y": [y + 1]
        }

    def __str__(self) -> str:
        return self.parameter

    def draw(self, hl=False):
        # Define characters
        h = chr(0x2501)
        v = chr(0x2502)
        tl = chr(0x250d)
        tr = chr(0x2511)
        bl = chr(0x2515)
        br = chr(0x2519)
        width = len(self.label) + 4

        # Draw top border
        STDSCR.addstr(self.y, self.x, tl + h * (width - 2) + tr)

        # Draw text with side borders
        STDSCR.addstr(self.y + 1, self.x, v + " ")
        if hl:
            STDSCR.addstr(self.label, curses.A_REVERSE)
        else:
            STDSCR.addstr(self.label)
        STDSCR.addstr(" " + v)

        # Draw bottom border
        STDSCR.addstr(self.y + 2, self.x, bl + h * (width - 2) + br)
        STDSCR.refresh()

    def click(self):
        for _ in range(2):
            self.draw(True)
            STDSCR.refresh()
            time.sleep(self.sleep_time)
            self.draw(False)
            STDSCR.refresh()
            time.sleep(self.sleep_time)

    def in_bounds(self, x, y) -> bool:
        return x in self.area["x"] and y in self.area["y"]


def host_game():
    pass  # TODO


def join_game():
    pass  # TODO


def local_game():
    pass  # TODO


def cpu_game():
    pass  # TODO


def intro():
    STDSCR.clear()
    lines = ["┌┬┐┬┌─┐  ┌┬┐┌─┐┌─┐  ┌┬┐┌─┐┌─┐", " │ ││     │ ├─┤│     │ │ │├┤ ", " ┴ ┴└─┘   ┴ ┴ ┴└─┘   ┴ └─┘└─┘"]
    for i in range(len(lines)):
        STDSCR.addstr(i, (MAX_X - len(lines[0])) // 2, lines[i])
    STDSCR.refresh()


def choose_game_mode() -> str:
    buttons = []

    host_str = "Host "
    host_button = Button("host", host_str, (MAX_X - len(host_str) - 4) // 2, 3 * (len(buttons) + 1) + 1)
    buttons.append(host_button)

    join_str = "Join "
    join_button = Button("join", join_str, (MAX_X - len(join_str) - 4) // 2, 3 * (len(buttons) + 1) + 1)
    buttons.append(join_button)

    local_str = "Local"
    local_button = Button("local", local_str, (MAX_X - len(local_str) - 4) // 2, 3 * (len(buttons) + 1) + 1)
    buttons.append(local_button)

    cpu_str = "CPU  "
    cpu_button = Button("cpu", cpu_str, (MAX_X - len(cpu_str) - 4) // 2, 3 * (len(buttons) + 1) + 1)
    buttons.append(cpu_button)

    while True:
        for button in buttons:
            button.draw()

        event = STDSCR.getch()
        mx, my = get_mouse_xy()

        if event == ord('q'):
            end_game()

        for button in buttons:
            if button.in_bounds(mx, my):
                button.click()
                return button


def end_game():
    print("\nThanks for playing Tic Tac Toe!\n")
    sys.exit(0)


def get_mouse_xy():
    _, mx, my, _, _ = curses.getmouse()
    return mx, my


def main(stdscr):
    global MAX_Y, MAX_X  # Height and width get global visibility
    global STDSCR
    MAX_Y, MAX_X = stdscr.getmaxyx()
    STDSCR = stdscr

    # Set up curses
    curses.mousemask(curses.REPORT_MOUSE_POSITION)  # Enable mouse events
    curses.curs_set(0)  # Hide cursor

    try:
        intro()
        STDSCR.refresh()

        game_mode = choose_game_mode()

        if game_mode == "host":
            host_game()
        elif game_mode == "join":
            join_game()
        elif game_mode == "local":
            local_game()
        else:
            cpu_game()

    except KeyboardInterrupt:
        pass

    finally:
        end_game()


if __name__ == "__main__":
    curses.wrapper(main)