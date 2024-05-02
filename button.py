import curses
import time

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
