import os
import time


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


def type_text(text, delay=0.05):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()  # Print a newline after typing the text


def main():
    board = [[' ']*3 for _ in range(3)]
    players = ['X', 'O']
    turn = 0

    while True:
        clear_screen()
        print_board(board)
        type_text(f"Player {players[turn]}'s turn")
        try:
            row = int(input("Enter row number (0, 1, 2): "))
            col = int(input("Enter column number (0, 1, 2): "))
        except ValueError:
            type_text("Please enter a number! Press enter to continue...")
            input()
            continue

        if row < 0 or row > 2 or col < 0 or col > 2:
            type_text("Invalid input. Please enter numbers between 0 and 2.")
            input()
            continue

        if board[row][col] != ' ':
            type_text("That cell is already taken. Please choose another one.")
            input()
            continue

        board[row][col] = players[turn]
        winner = check_winner(board)

        if winner:
            print_board(board)
            type_text(f"Player {winner} wins!")
            break

        if all(board[i][j] != ' ' for i in range(3) for j in range(3)):
            print_board(board)
            type_text("It's a tie!")
            break

        turn = (turn + 1) % 2


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        type_text("\nClosing game...\n")