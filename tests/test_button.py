import pytest
from unittest.mock import Mock, patch
from src.button import Button

@pytest.fixture
def mock_stdscr():
    return Mock()

def test_button_initialization(mock_stdscr):
    button = Button(mock_stdscr, "Test", 5, 5)
    assert button.stdscr == mock_stdscr
    assert button.parameter == "Test"
    assert button.label == "Test"
    assert button.x == 5
    assert button.y == 5
    assert button.area == {"x": [5, 6, 7, 8, 9, 10, 11, 12], "y": [5, 6, 7]}

def test_button_draw(mock_stdscr):
    button = Button(mock_stdscr, "Test", 5, 5)
    with patch.object(button.stdscr, 'addstr') as mocked_addstr:
        button.draw()
        assert mocked_addstr.call_count == 3
        assert mocked_addstr.call_args_list == [
            ((5, 5, '┏━━━━━━┓'),),
            ((6, 5, '┃ Test ┃'),),
            ((7, 5, '┗━━━━━━┛'),)
        ]

def test_button_click(mock_stdscr):
    button = Button(mock_stdscr, "Test", 5, 5)
    with patch.object(button, 'draw') as mock_draw, patch('time.sleep'):
        button.click()
        assert mock_draw.call_count == 4

def test_button_in_bounds(mock_stdscr):
    button = Button(mock_stdscr, "Test", 5, 5)
    assert button.in_bounds(6, 6)
    assert not button.in_bounds(4, 6)
    assert not button.in_bounds(6, 4)
    assert not button.in_bounds(10, 10)