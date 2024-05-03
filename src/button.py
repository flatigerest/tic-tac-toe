from curses import window, A_REVERSE
from time import sleep
from typing import Union

class Button:
    _sleep_time: float = 0.1

    def __init__(self, stdscr: window, label: str, x: int, y: int, parameter: Union[str, None]=None) -> None:
        """
        Initialize a Button object.

        Args:
            label (str): The label displayed on the button.
            x (int): The x-coordinate of the top-left corner of the button.
            y (int): The y-coordinate of the top-left corner of the button.
            parameter (str, optional): The parameter associated with the button. Defaults to None.
        """
        self.stdscr: window = stdscr
        self.parameter: str = parameter if parameter is not None else label
        self.label: str = label
        self.x: int = x
        self.y: int = y
        # Define the area of the button as a dictionary with x and y coordinates
        self.area: dict = {
            "x": [num for num in range(x, x + len(self.label) + 4)],
            "y": [num for num in range(y, y + 3)]
        }
        self.is_selected = False

    def __str__(self) -> str:
        """
        Return the parameter associated with the button as a string.
        """
        return self.parameter

    def select(self):
        self.is_selected = True

    def deselect(self):
        self.is_selected = False

    def draw(self, hl: bool=False):
        """
        Draw the button on the screen.

        Args:
            hl (bool, optional): If True, highlight the button. Defaults to False.
        """
        # Define characters for drawing the button border
        h = '━'
        v = '┃'
        tl = '┏'
        tr = '┓'
        bl = '┗'
        br = '┛'
        width: int = len(self.label) + 4  # Calculate the width of the button

        self.stdscr.addstr(self.y, self.x, tl + h * (width - 2) + tr)
        if hl or self.is_selected:
            self.stdscr.addstr(self.y + 2, self.x, bl + h * (width - 2) + br, A_REVERSE)
        else:
            self.stdscr.addstr(self.y + 1, self.x, f"{v} {self.label} {v}")

        self.stdscr.addstr(self.y + 2, self.x, bl + h * (width - 2) + br)
        self.stdscr.refresh()

    def click(self):
        """
        Simulate a button click by highlighting and unhighlighting the button.
        """
        for _ in range(2):
            self.draw(hl=True)  # Highlight the button
            self.stdscr.refresh()
            sleep(self._sleep_time)
            self.draw(hl=False)  # Unhighlight the button
            self.stdscr.refresh()
            sleep(self._sleep_time)

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
