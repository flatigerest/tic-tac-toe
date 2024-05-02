import curses
import requests
from ipaddress import ip_address

def center(stdscr: curses.window, num: int | float) -> int:
    """
    Calculate the center position of a screen given a width.

    Args:
        num (int): The width to center.

    Returns:
        int: The x-coordinate of the center position.
    """
    _, max_x = stdscr.getmaxyx()
    return (max_x - num) // 2


def clear_y(stdscr: curses.window, y: int) -> None:
    """
    Clear a line on the screen.

    Args:
        y (int): The y-coordinate of the line to clear.
    """
    _, max_x = stdscr.getmaxyx()
    stdscr.addstr(y, 0, " " * (max_x - 1))


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


def is_valid_ip(ip: str) -> bool:
    """
    Check if the given string is a valid IP address.

    Args:
        ip (str): The string to check.

    Returns:
        bool: True if the string is a valid IP address, False otherwise.
    """
    try:
        ip_address(ip)
        return True
    except ValueError:
        return False


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