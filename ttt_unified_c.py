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
        """
        Initialize a Button object.

        Args:
            parameter (str): The parameter associated with the button.
            label (str): The label displayed on the button.
            x (int): The x-coordinate of the top-left corner of the button.
            y (int): The y-coordinate of the top-left corner of the button.
        """
        self.parameter = parameter
        self.label = label
        self.x = x
        self.y = y
        self.area = {
            "x": [num for num in range(x + 1, x + len(self.label))],
            "y": [y + 1]
        }

    def __str__(self) -> str:
        """
        Return the parameter associated with the button as a string.
        """
        return self.parameter

    def draw(self, hl=False):
        """
        Draw the button on the screen.

        Args:
            hl (bool, optional): If True, highlight the button. Defaults to False.
        """
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
        """
        Simulate a button click by highlighting and unhighlighting the button.
        """
        for _ in range(2):
            self.draw(True)
            STDSCR.refresh()
            time.sleep(self._sleep_time)
            self.draw(False)
            STDSCR.refresh()
            time.sleep(self._sleep_time)

    def in_bounds(self, x, y) -> bool:
        """
        Check if the given coordinates are within the boundaries of the button.

        Args:
            x (int): The x-coordinate to check.
            y (int): The y-coordinate to check.

        Returns:
            bool: True if the coordinates are within the button, False otherwise.
        """
        return x in self.area["x"] and y in self.area["y"]


class Board:
    _board_width = 23
    _board_height = 11
    _cell_width = 8
    _cell_height = 4
    _board = [[' ']*3 for _ in range(3)]

    def __init__(self, x=None, y=None) -> None:
        """
        Initialize a Board object.

        Args:
            x (int, optional): The x-coordinate of the top-left corner of the board. Defaults to None.
            y (int, optional): The y-coordinate of the top-left corner of the board. Defaults to None.
        """
        self.x = center(self._board_width) if x is None else x
        self.y = center(self._board_height) if y is None else y
        self._lines = self._generate_board()

    def _generate_board(self) -> list:
        """
        Generate the ASCII representation of the game board.

        Returns:
            list: The lines representing the game board.
        """
        cross = chr(0x256c)
        horizontal = chr(0x2550)
        vertical = chr(0x2551)
        h_line = (horizontal * 7 + cross) * 2 + horizontal * 7
        blank_line = (" " * 7 + vertical) * 2
        return [blank_line] * 3 + [h_line] + [blank_line] * 3 + [h_line] + [blank_line] * 3

    def clear_board() -> None:
        """
        Clear the game board by resetting all cells to empty.
        """
        Board._board = [[' ']*3 for _ in range(3)]

    def is_empty(self, row, col) -> bool:
        """
        Check if a cell on the board is empty.

        Args:
            row (int): The row index of the cell.
            col (int): The column index of the cell.

        Returns:
            bool: True if the cell is empty, False otherwise.
        """
        return self._board[row][col] == " "

    def highlight_cell(self, row, col, undo=False) -> bool:
        """
        Highlight or unhighlight a cell on the board.

        Args:
            row (int): The row index of the cell.
            col (int): The column index of the cell.
            undo (bool, optional): If True, undo the highlighting. Defaults to False.

        Returns:
            bool: True if the cell is empty, False otherwise.
        """
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
        """
        Check if the given coordinates are within the boundaries of the board.

        Args:
            mx (int): The x-coordinate to check.
            my (int): The y-coordinate to check.

        Returns:
            bool: True if the coordinates are within the board, False otherwise.
        """
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
        """
        Get the row and column indices of the cell corresponding to the given coordinates.

        Args:
            mx (int): The x-coordinate to check.
            my (int): The y-coordinate to check.

        Returns:
            tuple: A tuple containing the row and column indices of the cell.
        """
        mx -= self.x
        my -= self.y
        row = my // self._cell_height
        col = mx // self._cell_width
        return row, col

    def update_board(self, player, row, col) -> None:
        """
        Update the value of a cell on the board with the specified player symbol.

        Args:
            player (str): The symbol representing the player.
            row (int): The row index of the cell.
            col (int): The column index of the cell.
        """
        self._board[row][col] = player

    def draw_board(self) -> None:
        """
        Draw the game board on the screen.
        """
        for i, line in enumerate(self._lines):
            STDSCR.addstr(self.y + i, self.x, line)
        STDSCR.refresh()

    def draw_values(self) -> None:
        """
        Draw the current values of the cells on the game board.
        """
        for i, row in enumerate(self._board):
            for j, val in enumerate(row):
                STDSCR.addstr(self.y + 1 + self._cell_height * i, self.x + 3 + self._cell_width * j, val)
        STDSCR.refresh()

    def get_winner(self) -> str | None:
        """
        Check if there is a winner on the game board.

        Returns:
            str | None: The symbol of the winning player or 'tie' if there's a tie, or None if no winner.
        """
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

        # Check for tie
        if all(self._board[i][j] != ' ' for i in range(3) for j in range(3)):
            return "tie"

        return None

    def get_board_width() -> int:
        """
        Get the width of the game board.

        Returns:
            int: The width of the game board.
        """
        return Board._board_width

    def get_board_height() -> int:
        """
        Get the height of the game board.

        Returns:
            int: The height of the game board.
        """
        return Board._board_height


def center(num) -> int:
    """
    Calculate the center position of a screen given a width.

    Args:
        num (int): The width to center.

    Returns:
        int: The x-coordinate of the center position.
    """
    return (MAX_X - num) // 2


def player_turn(player, board: Board) -> None:
    """
    Allow the specified player to take their turn on the game board.

    Args:
        player (str): The symbol representing the current player.
        board (Board): The game board on which the player is taking their turn.
    """
    prev_click = [None, None]
    while True:
        str = "It's Player {}'s turn.".format(player)
        STDSCR.addstr(Board.get_board_height() + board.y + 2, center(len(str)), str)
        STDSCR.refresh()

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
    """
    A class representing a banner to be displayed on the screen.
    """
    lines = ["╔─────────────────────────────╗",
             "│┌┬┐┬┌─┐  ┌┬┐┌─┐┌─┐  ┌┬┐┌─┐┌─┐│",
             "│ │ ││     │ ├─┤│     │ │ │├┤ │",
             "│ ┴ ┴└─┘   ┴ ┴ ┴└─┘   ┴ └─┘└─┘│",
             "╚─────────────────────────────╝"
    ]
    width = len(lines[0])
    height = len(lines)

    def draw() -> None:
        """
        Draw the banner on the screen.
        """
        for i, line in enumerate(Banner.lines):
            STDSCR.addstr(i, center(Banner.width), line)
        STDSCR.refresh()


def clear_y(y) -> None:
    """
    Clear a line on the screen.

    Args:
        y (int): The y-coordinate of the line to clear.
    """
    STDSCR.addstr(y, 0, " " * (MAX_X - 1))


def host_game():
    pass  # TODO


def join_game():
    pass  # TODO


def local_game():
    """
    Conducts a local game of Tic Tac Toe between two players.

    This function initializes the game, draws the game board, and handles player turns until there is a winner
    or a tie.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    def display_winner(player, y) -> None:
        """
        Display a message indicating the winner of the game.

        Args:
            player (str): The symbol representing the winning player.
            y (int): The y-coordinate of the message on the screen.

        Raises:
            KeyboardInterrupt: If the user quits the game by pressing any key.
        """
        clear_y(y)
        str = "Player {} wins! Click anywhere to continue...".format(player)
        STDSCR.addstr(y, center(len(str)), str)
        STDSCR.getch()

    def display_tie(y) -> None:
        """
        Display a message indicating that the game ended in a tie.

        Args:
            y (int): The y-coordinate of the message on the screen.

        Raises:
            KeyboardInterrupt: If the user quits the game by pressing any key.
        """
        clear_y(y)
        str = "It's a tie! Click anywhere to continue..."
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
        player_turn(players[turn], board)
        board.draw_values()
        winner = board.get_winner()

        if winner and winner != "tie":
            display_winner(winner, Board.get_board_height() + board.y + 2)
            Board.clear_board()
            break
        elif winner and winner == "tie":
            display_tie(Board.get_board_height() + board.y + 2)
            Board.clear_board()
            break

        turn = (turn + 1) % 2


def footer() -> None:
    """
    Display the footer at the bottom of the screen.

    The footer includes information about the developer and instructions to quit the game by pressing 'q'.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing any key.
    """
    STDSCR.addstr(MAX_Y - 1, 0, chr(0x00a9) + " flatiger 2024  |  Press 'q' at any time to quit")
    STDSCR.refresh()


def cpu_game():
    pass  # TODO


def play_again() -> bool:
    """
    Display a prompt asking the player if they want to play again.

    Returns:
        bool: True if the player chooses to play again, False otherwise.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
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
    """
    Display the game mode selection screen and wait for the player to choose a mode.

    Returns:
        str: The chosen game mode as a string.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
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
    """
    End the game and print a farewell message.

    Raises:
        SystemExit: Indicates a successful termination of the program.
    """
    print("\nThanks for playing Tic Tac Toe!\n")
    sys.exit(0)


def get_mouse_xy():
    """
    Get the x and y coordinates of the mouse cursor.

    Returns:
        tuple[int, int]: The x and y coordinates of the mouse cursor.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    _, mx, my, _, _ = curses.getmouse()
    return mx, my


def main(stdscr):
    """
    The main function responsible for running the Tic Tac Toe game.

    Args:
        stdscr: The standard screen object provided by the curses library.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
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