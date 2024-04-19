# Tic-tac-toe with socket!
# This is the client script.

import socket
import os
from time import sleep
import json


def play_game(conn):
    board = [[' ']*3 for _ in range(3)]
    players = ['X', 'O']
    turn = 0

    type_text("The host is choosing their character.")

    player = conn.recv(1024).decode()
    if player == players[0]:
        opponent = players[1]
    else:
        opponent = players[0]
    type_input(f"You are player {player}. Press enter to continue...")

    while True:
        clear_screen()
        print_board(board)

        if player == players[turn]:
            type_text("Your turn!")
            try:
                row = int(type_input("Enter row number (0, 1, 2): "))
                col = int(type_input("Enter column number (0, 1, 2): "))
            except ValueError:
                type_text("Please enter a number! Press enter to continue...")
                input()
                continue

            if row < 0 or row > 2 or col < 0 or col > 2:
                type_text("Invalid input. Please enter numbers between 0 and 2. Press enter to continue...")
                input()
                continue

            if board[row][col] != ' ':
                type_text("That cell is already taken. Press enter to continue...")
                input()
                continue

            conn.send(json.dumps((row, col)).encode())  # Send tuple of values
            board[row][col] = player

        else:
            print("Waiting for opponent...")
            opponent_choice = conn.recv(1024).decode()
            if not opponent_choice:
                break
            opponent_choice = json.loads(opponent_choice)
            row = opponent_choice[0]
            col = opponent_choice[1]
            board[row][col] = opponent

        winner = check_winner(board)
        if winner:
            clear_screen()
            print_board(board)
            if winner == player:
                type_text("\n🎉🎉 You win! 🎉🎉\n")
                break

            else:
                type_text("\nlmao imagine winning anyways 💀🤡🤡\n")
                break

        if all(board[i][j] != ' ' for i in range(3) for j in range(3)):
            clear_screen()
            print_board(board)
            type_text("\nIt's a tie 👔🤝🤝\n")
            break

        turn = (turn + 1) % 2


def print_board(board):
    for x in range(len(board)):
        row = board[x]
        print(" " + " | ".join(row) + " ")
        if x != len(board) - 1:
            print("-" * 11)


def check_winner(board):
    # Check rows
    for row in board:
        if len(set(row)) == 1 and row[0] != ' ':
            return row[0]

    # Check columns
    for col in range(3):
        if len(set([board[row][col] for row in range(3)])) == 1 and board[0][col] != ' ':
            return board[0][col]

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != ' ':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != ' ':
        return board[0][2]

    return None


def clear_screen():
    # Check the operating system
    if os.name == 'posix':  # Unix/Linux/Mac
        os.system('clear')
    elif os.name == 'nt':  # Windows
        os.system('cls')


def type_input(text, delay=0.02):
    type_text(text, delay)
    user_input = input()  # Wait for user input
    return user_input


def type_text(text, delay=0.02):
    for char in text:
        print(char, end='', flush=True)
        sleep(delay)
    print()  # Print a newline after typing the text


def main():
    try:
        clear_screen()
        host = type_input("Enter the host IP address: ")
        port = 12345

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            type_text("Connected to host!")
            play_game(s)

    except KeyboardInterrupt:
        clear_screen()
        type_text("\nClosing game...\n")


if __name__ == "__main__":
    main()