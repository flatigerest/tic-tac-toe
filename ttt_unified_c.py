import curses
import sys
import time
import socket
import json
import requests
import random
import ipaddress
import functools
from typing import List


def debug(func) -> any:
    """Print the function signature and return value (not mine)"""
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
    _sleep_time: float = 0.1

    def __init__(self, stdscr: curses.window, label: str, x: int, y: int, parameter: str | None=None) -> None:
        """
        Initialize a Button object.

        Args:
            label (str): The label displayed on the button.
            x (int): The x-coordinate of the top-left corner of the button.
            y (int): The y-coordinate of the top-left corner of the button.
            parameter (str, optional): The parameter associated with the button. Defaults to None.
        """
        self.stdscr: curses.window = stdscr
        self.parameter: str = parameter if parameter is not None else label
        self.label: str = label
        self.x: int = x
        self.y: int = y
        # Define the area of the button as a dictionary with x and y coordinates
        self.area: dict = {
            "x": [num for num in range(x + 1, x + len(self.label))],
            "y": [y + 1]
        }

    def __str__(self) -> str:
        """
        Return the parameter associated with the button as a string.
        """
        return self.parameter

    def draw(self, hl: bool=False):
        """
        Draw the button on the screen.

        Args:
            hl (bool, optional): If True, highlight the button. Defaults to False.
        """
        # Define characters for drawing the button border
        h: chr = chr(0x2501)
        v: chr = chr(0x2502)
        tl: chr = chr(0x250d)
        tr: chr = chr(0x2511)
        bl: chr = chr(0x2515)
        br: chr = chr(0x2519)
        width: int = len(self.label) + 4  # Calculate the width of the button

        # Draw top border
        self.stdscr.addstr(self.y, self.x, tl + h * (width - 2) + tr)

        # Draw text with side borders
        self.stdscr.addstr(self.y + 1, self.x, v + " ")
        if hl:
            self.stdscr.addstr(self.label, curses.A_REVERSE)
        else:
            self.stdscr.addstr(self.label)
        self.stdscr.addstr(" " + v)

        # Draw bottom border
        self.stdscr.addstr(self.y + 2, self.x, bl + h * (width - 2) + br)
        self.stdscr.refresh()

    def click(self):
        """
        Simulate a button click by highlighting and unhighlighting the button.
        """
        for _ in range(2):
            self.draw(hl=True)  # Highlight the button
            self.stdscr.refresh()
            time.sleep(self._sleep_time)
            self.draw(hl=False)  # Unhighlight the button
            self.stdscr.refresh()
            time.sleep(self._sleep_time)

    def in_bounds(self, x: int, y: int) -> bool:
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
    _board_width: int = 23
    _board_height: int = 11
    _cell_width: int = 8
    _cell_height: int = 4
    _board: List[List[str]] = [[' ']*3 for _ in range(3)]

    def __init__(self, stdscr: curses.window, x: int=None, y: int=None) -> None:
        """
        Initialize a Board object.

        Args:
            x (int, optional): The x-coordinate of the top-left corner of the board. Defaults to None.
            y (int, optional): The y-coordinate of the top-left corner of the board. Defaults to None.
        """
        self.stdscr: curses.window = stdscr
        # Set the coordinates of the top-left corner of the board
        self.x: int = center(self._board_width) if x is None else x
        self.y: int = center(self._board_height) if y is None else y
        # Generate the initial representation of the board
        self._lines: List[str] = self._generate_board()

    def _generate_board(self) -> list:
        """
        Generate the Unicode representation of the game board.

        Returns:
            list: The lines representing the game board.
        """
        cross: chr = chr(0x256c)
        horizontal: chr = chr(0x2550)
        vertical: chr = chr(0x2551)
        h_line: str = (horizontal * 7 + cross) * 2 + horizontal * 7
        blank_line: str = (" " * 7 + vertical) * 2
        return [blank_line] * 3 + [h_line] + [blank_line] * 3 + [h_line] + [blank_line] * 3

    def is_empty(self, row: int, col: int) -> bool:
        """
        Check if a cell on the board is empty.

        Args:
            row (int): The row index of the cell.
            col (int): The column index of the cell.

        Returns:
            bool: True if the cell is empty, False otherwise.
        """
        return self._board[row][col] == " "

    def clear_cell(self, row: int, col: int) -> None:
        self._board[row][col] = " "

    def highlight_cell(self, row: int, col: int, undo: bool=False) -> bool:
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
            y_offset: int = self.y + row * 4
            x_offset: int = self.x + col * 8
            for i in range(3):
                if undo:
                    self.stdscr.addstr(y_offset + i, x_offset, "       ")
                else:
                    self.stdscr.addstr(y_offset + i, x_offset, "       ", curses.A_REVERSE)
            self.stdscr.refresh()

    def in_bounds(self, x: int, y: int) -> bool:
        """
        Check if the given coordinates are within the boundaries of the board.

        Args:
            x (int): The x-coordinate to check.
            y (int): The y-coordinate to check.

        Returns:
            bool: True if the coordinates are within the board, False otherwise.
        """
        x -= self.x
        y -= self.y
        if (x < 0) or \
            (y < 0) or \
            (x > self._board_width) or \
            (y > self._board_height) or \
            (x % self._cell_width == self._cell_width - 1) or \
            (y % self._cell_height == self._cell_height - 1):
                return False
        else:
            return True

    def get_cell(self, x: int, y: int) -> tuple:
        """
        Get the row and column indices of the cell corresponding to the given coordinates.

        Args:
            x (int): The x-coordinate to check.
            y (int): The y-coordinate to check.

        Returns:
            tuple: A tuple containing the row and column indices of the cell.
        """
        x -= self.x
        y -= self.y
        row: int = y // self._cell_height
        col: int = x // self._cell_width
        return row, col

    def update_board(self, player: str | chr, row: int, col: int) -> None:
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
            self.stdscr.addstr(self.y + i, self.x, line)
        self.stdscr.refresh()

    def draw_values(self) -> None:
        """
        Draw the current values of the cells on the game board.
        """
        for i, row in enumerate(self._board):
            for j, val in enumerate(row):
                self.stdscr.addstr(self.y + 1 + self._cell_height * i, self.x + 3 + self._cell_width * j, val)
        self.stdscr.refresh()

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

    @staticmethod
    def get_board_width() -> int:
        """
        Get the width of the game board.

        Returns:
            int: The width of the game board.
        """
        return Board._board_width

    @staticmethod
    def get_board_height() -> int:
        """
        Get the height of the game board.

        Returns:
            int: The height of the game board.
        """
        return Board._board_height

    @staticmethod
    def clear_board() -> None:
        """
        Clear the game board by resetting all cells to empty.
        """
        Board._board = [[' ']*3 for _ in range(3)]


def center(num: int | float) -> int:
    """
    Calculate the center position of a screen given a width.

    Args:
        num (int): The width to center.

    Returns:
        int: The x-coordinate of the center position.
    """
    _, max_x = curses.getmaxyx()
    return (max_x - num) // 2


def player_turn(stdscr: curses.window, player: str | chr, board: Board) -> tuple:
    """
    Allow the specified player to take their turn on the game board.

    Args:
        player (str): The symbol representing the current player.
        board (Board): The game board on which the player is taking their turn.

    Returns:
        tuple: A tuple containing the row and column indices of the cell where the player made their move.
    """
    prev_click = [None, None]
    while True:
        y = Board.get_board_height() + board.y + 2
        clear_y(stdscr, y)
        str = "It's Player {}'s turn.".format(player)
        stdscr.addstr(y, center(len(str)), str)
        stdscr.refresh()

        event = stdscr.getch()
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
                    return row, col
            if prev_click[0] is not None:
                board.highlight_cell(prev_click[0], prev_click[1], undo=True)
            prev_click = [row, col]

            # Prevent double click by long press
            time.sleep(0.5)
        else:
            prev_click = [None, None]


class Banner:
    """
    A class representing a banner to be displayed on the screen.
    """
    lines: List[str] = ["╔─────────────────────────────╗",
             "│┌┬┐┬┌─┐  ┌┬┐┌─┐┌─┐  ┌┬┐┌─┐┌─┐│",
             "│ │ ││     │ ├─┤│     │ │ │├┤ │",
             "│ ┴ ┴└─┘   ┴ ┴ ┴└─┘   ┴ └─┘└─┘│",
             "╚─────────────────────────────╝"
    ]
    width: int = len(lines[0])
    height: int = len(lines)

    @staticmethod
    def draw(stdscr: curses.window) -> None:
        """
        Draw the banner on the screen.
        """
        for i, line in enumerate(Banner.lines):
            stdscr.addstr(i, center(Banner.width), line)
        stdscr.refresh()


def clear_y(stdscr: curses.window, y: int) -> None:
    """
    Clear a line on the screen.

    Args:
        y (int): The y-coordinate of the line to clear.
    """
    _, max_x = curses.getmaxyx()
    stdscr.addstr(y, 0, " " * (max_x - 1))


def footer(stdscr: curses.window) -> None:
    """
    Display the footer at the bottom of the screen.

    The footer includes information about the developer and instructions to quit the game by pressing 'q'.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    max_y, _ = curses.getmaxyx()
    stdscr.addstr(max_y - 1, 0, chr(0x00a9) + " flatiger 2024  |  Press 'q' at any time to quit")
    stdscr.refresh()


def get_public_ip() -> str | None:
    """
    Retrieve the public IP address of the current device.

    This function sends a request to 'https://httpbin.org/ip' to get the public IP address.
    If the request is successful (status code 200), it parses the JSON response to extract
    the public IP address. If the request fails or encounters an error, it prints an error
    message and returns None.

    Returns:
        str | None: The public IP address of the device if retrieved successfully, else None.
    """
    try:
        response = requests.get('https://httpbin.org/ip', timeout=5)
        if response.status_code == 200:
            ip_info = response.json()
            return ip_info.get('origin', None)
        else:
            print(f"Failed to retrieve public IP. Status code: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print("Timeout error: The request to retrieve the public IP timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while retrieving public IP: {e}")
        return None


def get_input(stdscr: curses.window, x: int, y: int) -> str:
    """
    Prompt the user for input at the specified screen coordinates.

    Parameters:
        x (int): The x-coordinate of the input prompt.
        y (int): The y-coordinate of the input prompt.

    Returns:
        str: The user-entered input string.

    Raises:
        None

    Description:
        This function prompts the user to enter text input at the specified
        coordinates on the screen using the curses library. It allows the user
        to input text and provides basic text editing functionality, including
        the ability to delete characters with the Backspace key. The input is
        terminated when the user presses the Enter key, and the entered string
        is returned.

        Example usage:
            input_str = get_input(5, 5)
    """
    curses.curs_set(1)
    user_input = ""

    while True:
        char = stdscr.getch()

        if char == 10:  # Enter key
            if user_input.strip():  # Check if input is not empty
                break
            else:
                continue

        # Backspace key
        if char == 127 or char == 8:
            if user_input:
                user_input = user_input[:-1]
                stdscr.addstr(y, x, " " * len(user_input))
                stdscr.addstr(y, x, user_input)
                stdscr.move(y, x + len(user_input))
            continue

        # Append to input
        user_input += chr(char)
        stdscr.addstr(y, x + len(user_input) - 1, chr(char))

    curses.curs_set(0)
    return user_input


def display_connection(stdscr: curses.window, conn: str):
    clear_draw_ui(stdscr)
    str = f"Connected to {conn}."
    stdscr.addstr(Banner.height + 2, center(len(str)), str)
    stdscr.refresh()
    time.sleep(0.5)


def clear_draw_ui(stdscr: curses.window) -> None:
    stdscr.clear()
    Banner.draw(stdscr)
    footer(stdscr)


def is_valid_ip(ip: str) -> bool:
    """
    Check if the given string is a valid IP address.

    Args:
        ip (str): The string to check.

    Returns:
        bool: True if the string is a valid IP address, False otherwise.
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def online_game(stdscr: curses.window, conn: socket.socket, player: str) -> None:
    players = ['X', 'O']
    turn = 0
    board = Board(y=Banner.height + 2)

    clear_draw_ui(stdscr)
    board.draw_board()
    text_y = Board.get_board_height() + board.y + 2
    while True:
        if player == players[turn]:
            string = f"Your turn! ({player})"
            clear_y(stdscr, text_y)
            stdscr.addstr(text_y, center(len(string)), string)
            row, col = player_turn(stdscr, player, board)
            conn.send(json.dumps((row, col)).encode())

        else:
            string = "Waiting for opponent..."
            clear_y(stdscr, text_y)
            stdscr.addstr(text_y, center(len(string)), string)

            opp_choice = conn.recv(1024).decode()
            if not opp_choice:
                string = "Connection failed! Exiting game..."
                clear_y(stdscr, text_y)
                stdscr.addstr(text_y, center(len(string)), string)
                time.sleep(1)
                end_game()

            opp_choice = json.loads(opp_choice)
            board.update_board(players[turn], opp_choice[0], opp_choice[1])

        board.draw_values()
        winner = board.get_winner()

        if winner is not None:
            clear_y(stdscr, text_y)

            if winner == player:
                string = "YOU WIN!!!"
            elif winner == 'tie':
                string = "IT'S A TIE"
            else:
                string = "lmao YOU LOSE"
            stdscr.addstr(text_y, center(len(string)), string)
            stdscr.getch()
            break

        stdscr.refresh()
        turn = (turn + 1) % 2


def host_game(stdscr: curses.window, port: int=12345):
    def display_ip():
        clear_draw_ui(stdscr)

        string = f"Your IP is: {get_public_ip()}."
        stdscr.addstr(Banner.height + 2, center(len(string)), string)
        string = f"Listening on port {port}."
        stdscr.addstr(Banner.height + 2, center(len(string)), string)
        stdscr.refresh()

    def choose_character() -> str:
        clear_draw_ui(stdscr)
        string = f"Choose your character:"
        stdscr.addstr(Banner.height + 2, center(len(string)), string)
        button_y = Banner.height + 5
        xo_button_length = len('x') + 2
        randomize_button_length = len('randomize') + 2
        total_button_length = xo_button_length * 2 + randomize_button_length + 2 * 2
        buttons = [
            Button(stdscr=stdscr, label="X", x=center(total_button_length) - total_button_length / 2, y=button_y),
            Button(stdscr=stdscr, label='Y', x=center(total_button_length) - total_button_length / 2 + xo_button_length, y=button_y),
            Button(stdscr=stdscr, label="Randomize", x=center(total_button_length) - randomize_button_length, y=button_y, parameter="R")
        ]
        for button in buttons:
            button.draw()

        while True:
            event = stdscr.getch()
            if event == ord('q'):
                end_game()
            elif event != curses.KEY_MOUSE:
                continue

            mx, my = get_mouse_xy()


            for button in buttons:
                if button.in_bounds(mx, my):
                    button.click()
                    if str(button) != 'R':
                        return str(button)
                    else:
                        return random.choice(players)

    host = "0.0.0.0"
    players = ['X', 'O']

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        display_ip()
        conn, addr = s.accept()

        with conn:
            display_connection(stdscr, conn)
            player = choose_character()

            if player == players[0]:
                opp = players[1]
            else:
                opp = players[0]

            conn.send(str(opp).encode())
            online_game(stdscr, conn, player)


def join_game(stdscr: curses,window):
    clear_draw_ui(stdscr)

    string = "Enter the host's IP address: "
    text_y = Banner.height + 2
    while True:
        while True:
            clear_y(stdscr, text_y)
            stdscr.addstr(text_y, center(len(string)), string)
            stdscr.refresh()
            host = get_input(stdscr, text_y + 1, center(len(string)))
            if is_valid_ip(host):
                break

        port = 12345
        string = f"Connecting to {host}..."
        stdscr.addstr(text_y, center(len(string)), string)
        stdscr.refresh()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # Set a timeout for the connection attempt
            try:
                s.connect((host, port))
            except TimeoutError:
                string = f"Couldn't connect to {host}: Connection timed out."
                stdscr.addstr(text_y, center(len(string)), string)
                stdscr.refresh()
                continue
            except Exception as e:
                string = f"An error occurred while connecting to {host}: {e}"
                stdscr.addstr(text_y, center(len(string)), string)
                stdscr.refresh()
                continue

            string = f"Connected! The host is choosing their character."
            stdscr.addstr(text_y, center(len(string)), string)
            stdscr.refresh()

            player = s.recv(1024).decode()
            string = f"You are player {player}. Click anywhere to continue."
            stdscr.addstr(text_y, center(len(string)), string)
            stdscr.refresh()
            stdscr.getch()

            online_game(stdscr, s, player)
            break


def local_game(stdscr: curses.window) -> None:
    """
    Conducts a local game of Tic Tac Toe between two players.

    This function initializes the game, draws the game board, and handles player turns until there is a winner
    or a tie.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    def display_winner(player: str | chr, y: int) -> None:
        """
        Display a message indicating the winner of the game.

        Args:
            player (str): The symbol representing the winning player.
            y (int): The y-coordinate of the message on the screen.

        Raises:
            KeyboardInterrupt: If the user quits the game by pressing any key.
        """
        clear_y(stdscr, y)
        string = "Player {} wins! Click anywhere to continue...".format(player)
        stdscr.addstr(y, center(len(string)), string)
        stdscr.getch()

    def display_tie(y: int) -> None:
        """
        Display a message indicating that the game ended in a tie.

        Args:
            y (int): The y-coordinate of the message on the screen.

        Raises:
            KeyboardInterrupt: If the user quits the game by pressing any key.
        """
        clear_y(stdscr, y)
        string = "It's a tie! Click anywhere to continue..."
        stdscr.addstr(y, center(len(string)), string)
        stdscr.getch()

    players = ['X', 'O']
    turn = 0
    board = Board(y=Banner.height + 2)

    clear_draw_ui(stdscr)
    board.draw_board()
    while True:
        clear_y(stdscr, Board.get_board_height() + board.y + 2)
        string = "It's Player {}'s turn.".format(players[turn])
        stdscr.addstr(Board.get_board_height() + board.y + 2, center(len(string)), string)
        stdscr.refresh()
        player_turn(stdscr, players[turn], board)
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


def cpu_game(stdscr: curses.window) -> None:
    """
    Conducts a game of Tic Tac Toe against the computer.

    This function initializes the game, draws the game board, and handles player and computer turns until
    there is a winner or a tie.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    def display_winner(player: str | chr, y: int) -> None:
        """
        Display a message indicating the winner of the game.

        Args:
            player (str): The symbol representing the winning player or 'CPU'.
            y (int): The y-coordinate of the message on the screen.

        Raises:
            KeyboardInterrupt: If the user quits the game by pressing any key.
        """
        clear_y(stdscr, y)
        if player == "CPU":
            string = "CPU wins! Click anywhere to continue..."
        else:
            string = "Player {} wins! Click anywhere to continue...".format(player)
        stdscr.addstr(y, center(len(string)), string)
        stdscr.getch()

    def display_tie(y: int) -> None:
        """
        Display a message indicating that the game ended in a tie.

        Args:
            y (int): The y-coordinate of the message on the screen.

        Raises:
            KeyboardInterrupt: If the user quits the game by pressing any key.
        """
        clear_y(stdscr, y)
        string = "It's a tie! Click anywhere to continue..."
        stdscr.addstr(y, center(len(string)), string)
        stdscr.getch()

    def computer_turn(board: Board, player: str, opponent: str) -> None:
        """
        Simulate the computer's turn in the game.

        Args:
            board (Board): The game board.
            player (str): The symbol representing the computer player.
            opponent (str): The symbol representing the human player.
        """
        y = Board.get_board_height() + board.y + 2
        clear_y(stdscr, y)
        string = "CPU's turn."
        stdscr.addstr(y, center(len(string)), string)
        stdscr.refresh()

        # Introduce a slight delay to mimic CPU's processing time
        time.sleep(0.5)

        # Try to win if possible
        if try_to_win(board, player):
            return

        # Block opponent from winning
        if try_to_block(board, opponent):
            return

        # If no winning or blocking moves available, choose a random empty cell
        empty_cells = [(row, col) for row in range(3) for col in range(3) if board.is_empty(row, col)]
        if empty_cells:
            row, col = random.choice(empty_cells)
            board.update_board(player, row, col)

    def try_to_win(board: Board, player: str) -> bool:
        """
        Attempt to make a winning move for the given player.

        Args:
            board (Board): The game board.
            player (str): The symbol representing the player.

        Returns:
            bool: True if a winning move was made, False otherwise.
        """
        # Check if the player can win in the next move and make that move
        for row in range(3):
            for col in range(3):
                if board.is_empty(row, col):
                    board.update_board(player, row, col)
                    if board.get_winner() == player:
                        return True
                    else:
                        # Reset the move if it doesn't result in a win
                        board.clear_cell(row, col)
        return False

    def try_to_block(board: Board, opponent: str) -> bool:
        """
        Attempt to block the opponent from winning.

        Args:
            board (Board): The game board.
            opponent (str): The symbol representing the opponent.

        Returns:
            bool: True if a blocking move was made, False otherwise.
        """
        # Check if the opponent can win in the next move and block that move
        for row in range(3):
            for col in range(3):
                if board.is_empty(row, col):
                    board.update_board(opponent, row, col)
                    if board.get_winner() == opponent:
                        # If the opponent can win, block their move
                        board.clear_cell(row, col)
                        board.update_board(opponent, row, col)
                        return True
                    else:
                        # Reset the move if it doesn't result in a win for the opponent
                        board.clear_cell(row, col)
        return False

    player = 'X'
    cpu = 'O'
    turn = 0
    board = Board(y=Banner.height + 2)

    clear_draw_ui(stdscr)
    board.draw_board()

    # Determine who goes first
    first_turn = random.randint(0, 1)
    if first_turn == 1:
        turn += 1

    while True:
        if turn % 2 == 0:
            string = "It's Player {}'s turn.".format(player)
            stdscr.addstr(Board.get_board_height() + board.y + 2, center(len(string)), string)
            stdscr.refresh()
            player_turn(player, board)
        else:
            computer_turn(board, cpu, player)

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

        turn += 1


def play_again(stdscr: curses.window) -> bool:
    """
    Display a prompt asking the player if they want to play again.

    Returns:
        bool: True if the player chooses to play again, False otherwise.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    stdscr.clear()
    footer(stdscr)
    lines = ["╔──────────────────────────────╗",
             "│┌─┐┬  ┌─┐┬ ┬  ┌─┐┌─┐┌─┐┬┌┐┌┌─┐│",
             "│├─┘│  ├─┤└┬┘  ├─┤│ ┬├─┤││││ ┌┘│",
             "│┴  ┴─┘┴ ┴ ┴   ┴ ┴└─┘┴ ┴┴┘└┘ o │",
             "╚──────────────────────────────╝"
    ]
    width = len(lines[0])
    height = len(lines)
    for i, line in enumerate(lines):
        stdscr.addstr(i, center(width), line)

    buttons = [Button(stdscr=stdscr, parameter="yes", label="Yes", x=center(7) - 5, y=height + 2),
               Button(stdscr=stdscr, parameter="no", label="No ", x=center(7) + 5, y=height + 2)]

    for button in buttons:
        button.draw()

    while True:
        event = stdscr.getch()
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


def choose_game_mode(stdscr: curses.window) -> str:
    """
    Display the game mode selection screen and wait for the player to choose a mode.

    Returns:
        str: The chosen game mode as a string.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    buttons = []

    host_str = "Host "
    host_button = Button(stdscr=stdscr, parameter="host", label=host_str, x=center(len(host_str) + 4), y=3 * len(buttons) + Banner.height + 1)
    buttons.append(host_button)

    join_str = "Join "
    join_button = Button(stdscr=stdscr, parameter="join", label=join_str, x=center(len(join_str) + 4), y=3 * len(buttons) + Banner.height + 1)
    buttons.append(join_button)

    local_str = "Local"
    local_button = Button(stdscr=stdscr, parameter="local", label=local_str, x=center(len(local_str) + 4), y=3 * len(buttons) + Banner.height + 1)
    buttons.append(local_button)

    cpu_str = "CPU  "
    cpu_button = Button(stdscr=stdscr, parameter="cpu", label=cpu_str, x=center(len(cpu_str) + 4), y=3 * len(buttons) + Banner.height + 1)
    buttons.append(cpu_button)

    for button in buttons:
        button.draw()

    while True:
        event = stdscr.getch()
        if event == ord('q'):
            end_game()
        elif event != curses.KEY_MOUSE:
            continue

        mx, my = get_mouse_xy()


        for button in buttons:
            if button.in_bounds(mx, my):
                button.click()
                return str(button)


def end_game() -> None:
    """
    End the game and print a farewell message.

    Raises:
        SystemExit: Indicates a successful termination of the program.
    """
    print("\nThanks for playing Tic Tac Toe!\n")
    sys.exit(0)


def get_mouse_xy() -> tuple:
    """
    Get the x and y coordinates of the mouse cursor.

    Returns:
        tuple[int, int]: The x and y coordinates of the mouse cursor.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    _, mx, my, _, _ = curses.getmouse()
    return mx, my


def main(stdscr: curses.window) -> None:
    """
    The main function responsible for running the Tic Tac Toe game.

    Args:
        stdscr: The standard screen object provided by the curses library.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    # Set up curses
    curses.mousemask(curses.REPORT_MOUSE_POSITION)  # Enable mouse events
    curses.curs_set(0)  # Hide cursor

    Banner.draw(stdscr)
    footer(stdscr)
    stdscr.refresh()

    try:
        while True:
            game_mode = choose_game_mode(stdscr)

            if game_mode == "host":
                host_game(stdscr)
            elif game_mode == "join":
                join_game(stdscr)
            elif game_mode == "local":
                local_game(stdscr)
            else:
                cpu_game(stdscr)

            if not play_again(stdscr):
                end_game()
                break
            else:
                stdscr.clear()

    except KeyboardInterrupt:
        end_game()


if __name__ == "__main__":
    curses.wrapper(main)