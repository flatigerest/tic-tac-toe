import curses
import sys
import time
import socket
import json
from requests import get as requestsget
from random import randint
import ipaddress
import functools

MAX_Y = None
MAX_X = None
STDSCR = None


def debug(func):
    """Print the function signature and return value"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        print(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        print(f"{func.__name__}() returned {repr(value)}")
        return value
    return wrapper_debug


class Button:
    _sleep_time = 0.1

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
            time.sleep(self._sleep_time)
            self.draw(False)
            STDSCR.refresh()
            time.sleep(self._sleep_time)

    def in_bounds(self, x, y) -> bool:
        return x in self.area["x"] and y in self.area["y"]


class Board:
    _board_width = 23
    _board_height = 11
    _cell_width = 8
    _cell_height = 4
    _board = [[' ']*3 for _ in range(3)]

    def __init__(self, x=None, y=None) -> None:
        self.x = center(self._board_width) if x is None else x
        self.y = center(self._board_height) if y is None else y
        self._lines = self._generate_board()

    def _generate_board(self) -> list:
        cross = chr(0x256c)
        horizontal = chr(0x2550)
        vertical = chr(0x2551)
        h_line = (horizontal * 7 + cross) * 2 + horizontal * 7
        blank_line = (" " * 7 + vertical) * 2
        return [blank_line] * 3 + [h_line] + [blank_line] * 3 + [h_line] + [blank_line] * 3

    def clear_board() -> None:
        Board._board = [[' ']*3 for _ in range(3)]

    def is_empty(self, row, col) -> bool:
        return self._board[row][col] == " "

    def highlight_cell(self, row, col, undo=False) -> bool:
        if self.is_empty(row, col):
            y_offset = self.y + row * 4
            x_offset = self.x + col * 8
            for i in range(3):
                if undo:
                    STDSCR.addstr(y_offset + i, x_offset, "       ")
                else:
                    STDSCR.addstr(y_offset + i, x_offset, "       ", curses.A_REVERSE)
            STDSCR.refresh()

    def in_bounds(self, mx, my) -> bool:
        mx -= self.x
        my -= self.y
        if (mx < 0) or \
            (my < 0) or \
            (mx > self._board_width) or \
            (my > self._board_height) or \
            (mx % self._cell_width == self._cell_width - 1) or \
            (my % self._cell_height == self._cell_height - 1):
                return False
        else:
            return True

    def get_cell(self, mx, my) -> tuple:
        mx -= self.x
        my -= self.y
        row = my // self._cell_height
        col = mx // self._cell_width
        return row, col

    def update_board(self, player, row, col) -> None:
        self._board[row][col] = player

    def draw_board(self) -> None:
        for i, line in enumerate(self._lines):
            STDSCR.addstr(self.y + i, self.x, line)
        STDSCR.refresh()

    def draw_values(self) -> None:
        for i, row in enumerate(self._board):
            for j, val in enumerate(row):
                STDSCR.addstr(self.y + 1 + self._cell_height * i, self.x + 3 + self._cell_width * j, val)
        STDSCR.refresh()

    def get_winner(self) -> str | None:
        # Check rows
        for row in self._board:
            if len(set(row)) == 1 and row[0] != ' ':
                return row[0]

        # Check columns
        for col in range(3):
            if len(set([self._board[row][col] for row in range(3)])) == 1 and self._board[0][col] != ' ':
                return self._board[0][col]

        # Check diagonals
        if self._board[0][0] == self._board[1][1] == self._board[2][2] != ' ':
            return self._board[0][0]
        if self._board[0][2] == self._board[1][1] == self._board[2][0] != ' ':
            return self._board[0][2]

        return None

    def get_board_width() -> int:
        return Board._board_width

    def get_board_height() -> int:
        return Board._board_height


def center(num) -> int:
    return (MAX_X - num) // 2


def player_turn(player, board: Board) -> None:
    prev_click = [None, None]
    while True:
        event = STDSCR.getch()
        mx, my = get_mouse_xy()

        if event == ord('q'):
            end_game()

        if board.in_bounds(mx, my):
            row, col = board.get_cell(mx, my)
            if board.is_empty(row, col):
                board.highlight_cell(row, col)
                if prev_click == [row, col]:
                    board.highlight_cell(row, col, undo=True)
                    board.update_board(player, row, col)
                    return
            if prev_click[0] is not None:
                board.highlight_cell(prev_click[0], prev_click[1], undo=True)
            prev_click = [row, col]

            # Prevent double click by longpress
            time.sleep(0.5)
        else:
            prev_click = [None, None]


class Banner:
    lines = ["╔─────────────────────────────╗",
             "│┌┬┐┬┌─┐  ┌┬┐┌─┐┌─┐  ┌┬┐┌─┐┌─┐│",
             "│ │ ││     │ ├─┤│     │ │ │├┤ │",
             "│ ┴ ┴└─┘   ┴ ┴ ┴└─┘   ┴ └─┘└─┘│",
             "╚─────────────────────────────╝"
    ]
    width = len(lines[0])
    height = len(lines)

    def draw() -> None:
        STDSCR.clear()
        for i, line in enumerate(Banner.lines):
            STDSCR.addstr(i, center(Banner.width), line)
        STDSCR.refresh()


def host_game():
    pass  # TODO


def join_game():
    pass  # TODO


def local_game():

    def display_winner(player, y) -> None:
        str = "Player {} wins!".format(player)
        STDSCR.addstr(y, center(len(str)), str)
        STDSCR.getch()

    players = ['X', 'O']
    turn = 0
    board = Board(y=Banner.height + 2)

    STDSCR.clear()
    footer()
    Banner.draw()
    board.draw_board()
    while True:
        board.draw_values()
        player_turn(players[turn], board)

        winner = board.get_winner()
        if winner:
            board.draw_values()
            display_winner(players[turn], Board.get_board_height() + board.y + 2)
            Board.clear_board()
            break

        turn = (turn + 1) % 2


def footer() -> None:
    STDSCR.addstr(MAX_Y - 1, 0, chr(0x00a9) + " flatiger 2024  |  Press 'q' at any time to quit")
    STDSCR.refresh()


def cpu_game():
    pass  # TODO


def play_again() -> bool:
    STDSCR.clear()
    footer()
    lines = ["╔──────────────────────────────╗",
             "│┌─┐┬  ┌─┐┬ ┬  ┌─┐┌─┐┌─┐┬┌┐┌┌─┐│",
             "│├─┘│  ├─┤└┬┘  ├─┤│ ┬├─┤││││ ┌┘│",
             "│┴  ┴─┘┴ ┴ ┴   ┴ ┴└─┘┴ ┴┴┘└┘ o │",
             "╚──────────────────────────────╝"
    ]
    width = len(lines[0])
    height = len(lines)
    for i, line in enumerate(lines):
        STDSCR.addstr(i, center(width), line)

    buttons = [Button("yes", "Yes", center(7) - 5, height + 2),
               Button("no", "No ", center(7) + 5, height + 2)]

    for button in buttons:
        button.draw()

    while True:
        event = STDSCR.getch()
        if event == ord('q'):
            end_game()
        elif event != curses.KEY_MOUSE:
            continue

        mx, my = get_mouse_xy()
        for button in buttons:
            if button.in_bounds(mx, my):
                button.click()
                if str(button) == "yes":
                    return True
                elif str(button) == "no":
                    return False


def choose_game_mode() -> str:
    buttons = []

    host_str = "Host "
    host_button = Button("host", host_str, center(len(host_str) + 4), 3 * len(buttons) + Banner.height + 1)
    buttons.append(host_button)

    join_str = "Join "
    join_button = Button("join", join_str, center(len(join_str) + 4), 3 * len(buttons) + Banner.height + 1)
    buttons.append(join_button)

    local_str = "Local"
    local_button = Button("local", local_str, center(len(local_str) + 4), 3 * len(buttons) + Banner.height + 1)
    buttons.append(local_button)

    cpu_str = "CPU  "
    cpu_button = Button("cpu", cpu_str, center(len(cpu_str) + 4), 3 * len(buttons) + Banner.height + 1)
    buttons.append(cpu_button)

    for button in buttons:
        button.draw()

    while True:
        event = STDSCR.getch()
        if event == ord('q'):
            end_game()
        elif event != curses.KEY_MOUSE:
            continue

        mx, my = get_mouse_xy()


        for button in buttons:
            if button.in_bounds(mx, my):
                button.click()
                return str(button)


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
        while True:
            Banner.draw()
            footer()
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

            if not play_again():
                break

    except KeyboardInterrupt:
        end_game()


if __name__ == "__main__":
    curses.wrapper(main)