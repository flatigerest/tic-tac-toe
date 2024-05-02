"""
THIS ONE ISN'T WORKING AND IDK WHY
"""

import pytest
import curses
from unittest.mock import patch
from src.board import Board

@pytest.fixture
def mock_stdscr():
    stdscr = curses.initscr()  # Initialize curses
    mock_win = curses.newwin(20, 40, 0, 0)  # Create a mock window
    stdscr.refresh()  # Refresh the screen
    yield mock_win  # Return the mock window
    curses.endwin()  # Clean up curses after the test

def test_board_initialization(mock_stdscr):
    board = Board(mock_stdscr)
    assert board.stdscr == mock_stdscr
    assert board.x == 8  # Adjust based on your actual center calculation
    assert board.y == 5  # Adjust based on your actual center calculation
    assert len(board._lines) == 9

def test_is_empty():
    board = Board(None)
    assert board.is_empty(0, 0)
    assert not board.is_empty(1, 1)

def test_clear_cell():
    board = Board(None)
    board._board[0][0] = 'X'
    board.clear_cell(0, 0)
    assert board.is_empty(0, 0)

def test_highlight_cell(mock_stdscr):
    board = Board(mock_stdscr)
    with patch.object(board.stdscr, 'addstr') as mocked_addstr:
        board.highlight_cell(0, 0)
        assert mocked_addstr.call_count == 3  # 3 lines drawn for highlighting

def test_in_bounds():
    board = Board(None)
    assert board.in_bounds(10, 10)
    assert not board.in_bounds(-1, 0)
    assert not board.in_bounds(10, 30)

def test_get_cell():
    board = Board(None)
    assert board.get_cell(10, 10) == (1, 1)
    assert board.get_cell(2, 2) == (0, 0)

def test_update_board():
    board = Board(None)
    board.update_board('X', 1, 1)
    assert board._board[1][1] == 'X'

def test_get_winner():
    board = Board(None)
    board._board = [['X', 'X', 'X'], [' ', ' ', ' '], [' ', ' ', ' ']]
    assert board.get_winner() == 'X'

def test_get_board_width():
    assert Board.get_board_width() == 23

def test_get_board_height():
    assert Board.get_board_height() == 11

def test_clear_board():
    Board.clear_board()
    assert all(cell == ' ' for row in Board._board for cell in row)