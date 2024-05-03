import curses
from time import sleep
from typing import List, Union
import socket
from json import loads, dumps
from random import choice, randint
import sys
from platform import system

from src.board import Board
from src.button import Button
import src.utils as utils


def play_game(stdscr: curses.window) -> None:
    # Check if OS is mac bc curses is gay
    is_mac = False
    if system() == "Darwin":
        is_mac = True

    # Set up curses
    curses.mousemask(curses.BUTTON1_CLICKED)  # Enable mouse events
    print('\033[?1003h')
    curses.curs_set(0)  # Hide cursor
    stdscr.keypad(1)

    Banner.draw(stdscr)
    footer(stdscr)
    stdscr.refresh()

    try:
        while True:
            game_mode = choose_game_mode(stdscr, is_mac)

            if game_mode == "host":
                host_game(stdscr, is_mac)
            elif game_mode == "join":
                join_game(stdscr, is_mac)
            elif game_mode == "local":
                local_game(stdscr, is_mac)
            else:
                cpu_game(stdscr, is_mac)

            if not play_again(stdscr):
                end_game()
                break
            else:
                stdscr.clear()

    except KeyboardInterrupt:
        end_game()


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
            stdscr.addstr(i, utils.center(stdscr, Banner.width), line)
        stdscr.refresh()


def player_turn(stdscr: curses.window, player: Union[str, chr], board: Board) -> tuple:
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
        utils.clear_y(stdscr, y)
        str = "It's Player {}'s turn.".format(player)
        stdscr.addstr(y, utils.center(stdscr, len(str)), str)
        stdscr.refresh()

        event = stdscr.getch()
        mx, my = utils.get_mouse_xy()


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
            sleep(0.5)
        else:
            prev_click = [None, None]


def footer(stdscr: curses.window) -> None:
    """
    Display the footer at the bottom of the screen.

    The footer includes information about the developer and instructions to quit the game by pressing 'q'.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    max_y, _ = stdscr.getmaxyx()
    stdscr.addstr(max_y - 1, 0, chr(0x00a9) + " flatiger 2024  |  Press 'q' at any time to quit")
    stdscr.refresh()


def display_connection(stdscr: curses.window, conn: str):
    clear_draw_ui(stdscr)
    str = f"Connected to {conn}."
    stdscr.addstr(Banner.height + 2, utils.center(stdscr, len(str)), str)
    stdscr.refresh()
    sleep(0.5)


def clear_draw_ui(stdscr: curses.window) -> None:
    stdscr.clear()
    Banner.draw(stdscr)
    footer(stdscr)


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
            utils.clear_y(stdscr, text_y)
            stdscr.addstr(text_y, utils.center(stdscr, len(string)), string)
            row, col = player_turn(stdscr, player, board)
            conn.send(dumps((row, col)).encode())

        else:
            string = "Waiting for opponent..."
            utils.clear_y(stdscr, text_y)
            stdscr.addstr(text_y, utils.center(stdscr, len(string)), string)

            opp_choice = conn.recv(1024).decode()
            if not opp_choice:
                string = "Connection failed! Exiting game..."
                utils.clear_y(stdscr, text_y)
                stdscr.addstr(text_y, utils.center(stdscr, len(string)), string)
                sleep(1)
                end_game()

            opp_choice = loads(opp_choice)
            board.update_board(players[turn], opp_choice[0], opp_choice[1])

        board.draw_values()
        winner = board.get_winner()

        if winner is not None:
            utils.clear_y(stdscr, text_y)

            if winner == player:
                string = "YOU WIN!!!"
            elif winner == 'tie':
                string = "IT'S A TIE"
            else:
                string = "lmao YOU LOSE"
            stdscr.addstr(text_y, utils.center(stdscr, len(string)), string)
            stdscr.getch()
            break

        stdscr.refresh()
        turn = (turn + 1) % 2


def host_game(stdscr: curses.window, is_mac, port: int=12345):
    def display_ip():
        clear_draw_ui(stdscr)

        string = f"Your IP is: {utils.get_public_ip()}."
        stdscr.addstr(Banner.height + 2, utils.center(stdscr, len(string)), string)
        string = f"Listening on port {port}."
        stdscr.addstr(Banner.height + 3, utils.center(stdscr, len(string)), string)
        stdscr.refresh()

    def choose_character() -> str:
        clear_draw_ui(stdscr)
        string = f"Choose your character:"
        stdscr.addstr(Banner.height + 2, utils.center(stdscr, len(string)), string)
        button_y = Banner.height + 5
        xo_button_length = len('x') + 2
        randomize_button_length = len('randomize') + 2
        total_button_length = xo_button_length * 2 + randomize_button_length + 2 * 2
        buttons = [
            Button(stdscr=stdscr, label="X", x=utils.center(stdscr, total_button_length) - total_button_length / 2, y=button_y),
            Button(stdscr=stdscr, label='Y', x=utils.center(stdscr, total_button_length) - total_button_length / 2 + xo_button_length, y=button_y),
            Button(stdscr=stdscr, label="Randomize", x=utils.center(stdscr, total_button_length) - randomize_button_length, y=button_y, parameter="R")
        ]
        for button in buttons:
            button.draw()

        while True:
            event = stdscr.getch()
            if event == ord('q'):
                end_game()
            elif event != curses.KEY_MOUSE:
                continue

            mx, my = utils.get_mouse_xy()


            for button in buttons:
                if button.in_bounds(mx, my):
                    button.click()
                    if str(button) != 'R':
                        return str(button)
                    else:
                        return choice(players)

    host = "0.0.0.0"
    players = ['X', 'O']

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))

        # Set curses and socket to non-blocking to allow for 'q' buttonpress
        stdscr.nodelay(1)
        s.setblocking(False)

        s.listen()
        display_ip()
        while True:
            ch = stdscr.getch()
            if ch and ch == ord('q'):
                end_game()

            try:
                conn, addr = s.accept()
                if conn:
                    break
            except BlockingIOError:
                continue

        # Re-enable blocking
        stdscr.nodelay(0)
        s.setblocking(True)
        with conn:
            display_connection(stdscr, conn)
            player = choose_character()

            if player == players[0]:
                opp = players[1]
            else:
                opp = players[0]

            conn.send(str(opp).encode())
            online_game(stdscr, conn, player)


def join_game(stdscr: curses.window, is_mac):
    clear_draw_ui(stdscr)

    string = "Enter the host's IP address: "
    text_y = Banner.height + 2
    while True:
        while True:
            utils.clear_y(stdscr, text_y)
            stdscr.addstr(text_y, utils.center(stdscr, len(string)), string)
            stdscr.refresh()
            host = utils.get_input(stdscr, text_y + 1, utils.center(stdscr, len(string)))
            if utils.is_valid_ip(host):
                break

        port = 12345
        string = f"Connecting to {host}..."
        stdscr.addstr(text_y, utils.center(stdscr, len(string)), string)
        stdscr.refresh()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # Set a timeout for the connection attempt
            try:
                s.connect((host, port))
            except TimeoutError:
                string = f"Couldn't connect to {host}: Connection timed out."
                stdscr.addstr(text_y, utils.center(stdscr, len(string)), string)
                stdscr.refresh()
                continue
            except Exception as e:
                string = f"An error occurred while connecting to {host}: {e}"
                stdscr.addstr(text_y, utils.center(stdscr, len(string)), string)
                stdscr.refresh()
                continue

            string = f"Connected! The host is choosing their character."
            stdscr.addstr(text_y, utils.center(stdscr, len(string)), string)
            stdscr.refresh()

            player = s.recv(1024).decode()
            string = f"You are player {player}. Click anywhere to continue."
            stdscr.addstr(text_y, utils.center(stdscr, len(string)), string)
            stdscr.refresh()
            stdscr.getch()

            online_game(stdscr, s, player)
            break


def local_game(stdscr: curses.window, is_mac) -> None:
    """
    Conducts a local game of Tic Tac Toe between two players.

    This function initializes the game, draws the game board, and handles player turns until there is a winner
    or a tie.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    def display_winner(player: Union[str, chr], y: int) -> None:
        """
        Display a message indicating the winner of the game.

        Args:
            player (str): The symbol representing the winning player.
            y (int): The y-coordinate of the message on the screen.

        Raises:
            KeyboardInterrupt: If the user quits the game by pressing any key.
        """
        utils.clear_y(stdscr, y)
        string = "Player {} wins! Click anywhere to continue...".format(player)
        stdscr.addstr(y, utils.center(stdscr, len(string)), string)
        stdscr.getch()

    def display_tie(y: int) -> None:
        """
        Display a message indicating that the game ended in a tie.

        Args:
            y (int): The y-coordinate of the message on the screen.

        Raises:
            KeyboardInterrupt: If the user quits the game by pressing any key.
        """
        utils.clear_y(stdscr, y)
        string = "It's a tie! Click anywhere to continue..."
        stdscr.addstr(y, utils.center(stdscr, len(string)), string)
        stdscr.getch()

    players = ['X', 'O']
    turn = 0
    board = Board(stdscr, y=Banner.height + 2)

    clear_draw_ui(stdscr)
    board.draw_board()
    while True:
        utils.clear_y(stdscr, Board.get_board_height() + board.y + 2)
        string = "It's Player {}'s turn.".format(players[turn])
        stdscr.addstr(Board.get_board_height() + board.y + 2, utils.center(stdscr, len(string)), string)
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


def cpu_game(stdscr: curses.window, is_mac) -> None:
    """
    Conducts a game of Tic Tac Toe against the computer.

    This function initializes the game, draws the game board, and handles player and computer turns until
    there is a winner or a tie.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    def display_winner(player: Union[str, chr], y: int) -> None:
        """
        Display a message indicating the winner of the game.

        Args:
            player (str): The symbol representing the winning player or 'CPU'.
            y (int): The y-coordinate of the message on the screen.

        Raises:
            KeyboardInterrupt: If the user quits the game by pressing any key.
        """
        utils.clear_y(stdscr, y)
        if player == "CPU":
            string = "CPU wins! Click anywhere to continue..."
        else:
            string = "Player {} wins! Click anywhere to continue...".format(player)
        stdscr.addstr(y, utils.center(stdscr, len(string)), string)
        stdscr.getch()

    def display_tie(y: int) -> None:
        """
        Display a message indicating that the game ended in a tie.

        Args:
            y (int): The y-coordinate of the message on the screen.

        Raises:
            KeyboardInterrupt: If the user quits the game by pressing any key.
        """
        utils.clear_y(stdscr, y)
        string = "It's a tie! Click anywhere to continue..."
        stdscr.addstr(y, utils.center(stdscr, len(string)), string)
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
        utils.clear_y(stdscr, y)
        string = "CPU's turn."
        stdscr.addstr(y, utils.center(stdscr, len(string)), string)
        stdscr.refresh()

        # Introduce a slight delay to mimic CPU's processing time
        sleep(0.5)

        # Try to win if possible
        if try_to_win(board, player):
            return

        # Block opponent from winning
        if try_to_block(board, opponent):
            return

        # If no winning or blocking moves available, choose a random empty cell
        empty_cells = [(row, col) for row in range(3) for col in range(3) if board.is_empty(row, col)]
        if empty_cells:
            row, col = choice(empty_cells)
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
    first_turn = randint(0, 1)
    if first_turn == 1:
        turn += 1

    while True:
        if turn % 2 == 0:
            string = "It's Player {}'s turn.".format(player)
            stdscr.addstr(Board.get_board_height() + board.y + 2, utils.center(stdscr, len(string)), string)
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
        stdscr.addstr(i, utils.center(stdscr, width), line)

    buttons = [Button(stdscr=stdscr, parameter="yes", label="Yes", x=utils.center(stdscr, 7) - 5, y=height + 2),
               Button(stdscr=stdscr, parameter="no", label="No ", x=utils.center(stdscr, 7) + 5, y=height + 2)]

    for button in buttons:
        button.draw()

    while True:
        event = stdscr.getch()
        if event == ord('q'):
            end_game()
        elif event != curses.KEY_MOUSE:
            continue

        mx, my = utils.get_mouse_xy()
        for button in buttons:
            if button.in_bounds(mx, my):
                button.click()
                if str(button) == "yes":
                    return True
                elif str(button) == "no":
                    return False


def choose_game_mode(stdscr: curses.window, is_mac: bool=False) -> str:
    """
    Display the game mode selection screen and wait for the player to choose a mode.

    Returns:
        str: The chosen game mode as a string.

    Raises:
        KeyboardInterrupt: If the user quits the game by pressing 'q'.
    """
    buttons = []

    host_str = "Host "
    host_button = Button(stdscr=stdscr, parameter="host", label=host_str, x=utils.center(stdscr, len(host_str) + 4), y=3 * len(buttons) + Banner.height + 1)
    buttons.append(host_button)

    join_str = "Join "
    join_button = Button(stdscr=stdscr, parameter="join", label=join_str, x=utils.center(stdscr, len(join_str) + 4), y=3 * len(buttons) + Banner.height + 1)
    buttons.append(join_button)

    local_str = "Local"
    local_button = Button(stdscr=stdscr, parameter="local", label=local_str, x=utils.center(stdscr, len(local_str) + 4), y=3 * len(buttons) + Banner.height + 1)
    buttons.append(local_button)

    cpu_str = "CPU  "
    cpu_button = Button(stdscr=stdscr, parameter="cpu", label=cpu_str, x=utils.center(stdscr, len(cpu_str) + 4), y=3 * len(buttons) + Banner.height + 1)
    buttons.append(cpu_button)

    selected_button = 0
    if is_mac:
        buttons[selected_button].select()

    while True:
        # Draw buttons
        clear_draw_ui(stdscr)
        for button in buttons:
            button.draw()

        event = stdscr.getch()
        if event == ord('q'):
            end_game()

        if not is_mac:
            if event != curses.KEY_MOUSE:
                continue

            mx, my = utils.get_mouse_xy()

            for button in buttons:
                if button.in_bounds(mx, my):
                    button.click()
                    return str(button)

        else:
            # Select
            if event == curses.KEY_UP:
                buttons[selected_button].deselect()
                selected_button -= 1
                if selected_button < 0:
                    selected_button = len(buttons) - 1
                buttons[selected_button].select()
                print("reached")

            # Deselect
            elif event == curses.KEY_DOWN:
                buttons[selected_button].deselect()
                selected_button += 1
                if selected_button > len(buttons) - 1:
                    selected_button = 0
                buttons[selected_button].select()

            # Click
            elif event == ord('\n'):
                buttons[selected_button].click()
                return str(buttons[selected_button])


def end_game() -> None:
    """
    End the game and print a farewell message.

    Raises:
        SystemExit: Indicates a successful termination of the program.
    """
    print("\nThanks for playing Tic Tac Toe!\n")
    sys.exit(0)