from typing import List, Union
from curses import window, A_REVERSE
from src.utils import center


class Board:
    _board_width: int = 23
    _board_height: int = 11
    _cell_width: int = 8
    _cell_height: int = 4
    _board: List[List[str]] = [[' ']*3 for _ in range(3)]

    def __init__(self, stdscr: window, x: int=None, y: int=None) -> None:
        """
        Initialize a Board object.

        Args:
            x (int, optional): The x-coordinate of the top-left corner of the board. Defaults to None.
            y (int, optional): The y-coordinate of the top-left corner of the board. Defaults to None.
        """
        self.stdscr: window = stdscr
        # Set the coordinates of the top-left corner of the board
        self.x: int = center(stdscr, self._board_width) if x is None else x
        self.y: int = center(stdscr, self._board_height) if y is None else y
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
                    self.stdscr.addstr(y_offset + i, x_offset, "       ", A_REVERSE)
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

    def update_board(self, player: Union[str, chr], row: int, col: int) -> None:
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

    def get_winner(self) -> Union[str, None]:
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