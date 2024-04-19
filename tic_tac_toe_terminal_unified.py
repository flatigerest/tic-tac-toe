# Tic-tac-toe with socket!
# This is the joint/unified script.

import socket
import os
from time import sleep
import json
from requests import get as requestsget
from random import randint


def play_game(conn, player):
    board = [[' ']*3 for _ in range(3)]
    players = ['X', 'O']
    turn = 0

    if player == players[0]:
        opponent = player[1]
    else:
        opponent = players[0]

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


def get_public_ip():
    try:
        response = requestsget('https://httpbin.org/ip')
        if response.status_code == 200:
            ip_info = response.json()
            return ip_info['origin']
        else:
            print(f"Failed to retrieve public IP. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


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


def join_game():
    clear_screen()
    host = type_input("Enter the host IP address: ")
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        type_text("Connected to host!")

        players = ['X', 'O']
        type_text("The host is choosing their character.")
        player = s.recv(1024).decode()
        if player == players[0]:
            opponent = players[1]
        else:
            opponent = players[0]
        type_input(f"You are player {player}. Press enter to continue...")

        play_game(conn=s, player=player)


def host_game():
    host = "0.0.0.0"
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        type_text(f"Server listening on {get_public_ip()}:{port}")
        conn, addr = s.accept()
        with conn:
            type_text(f"Connected to {addr}")
            players = ['X', 'O']
            type_text("Choose your character (X or O), or type enter for random: ")
            character_choice = input().strip().upper()
            if character_choice not in players:
                player = players[randint(0,1)]
                type_text(f"You are player {player}!")
            else:
                player = character_choice

            if player == players[0]:
                opponent = players[1]
            else:
                opponent = players[0]

            conn.send(str(opponent).encode())
            play_game(conn, player)


def type_input(text, delay=0.02):
    type_text(text, delay)
    user_input = input()  # Wait for user input
    return user_input


def type_text(text, delay=0.02):
    for char in text:
        print(char, end='', flush=True)
        sleep(delay)
    print()  # Print a newline after typing the text


def clear_screen():
    # Check the operating system
    if os.name == 'posix':  # Unix/Linux/Mac
        os.system('clear')
    elif os.name == 'nt':  # Windows
        os.system('cls')


def intro():
    clear_screen()
    type_text("Welcome to terminal tic-tac-toe!")


def main():
    try:
        intro()
        while True:
            game_modes = ["host", "client"]
            game_mode = type_input("Enter \"host\" if you wish to host a game, or type \"client\" to join someone's game.").strip().lower()
            if game_mode not in game_modes:
                type_text("Invalid input!")
            else:
                break

        if game_mode is "host":
            host_game()
        else:
            join_game()

    except KeyboardInterrupt:
        clear_screen()
        type_text("\nClosing game...\n")


if __name__ == "__main__":
    main()