import tkinter as tk
from tkinter import messagebox
import socket
from random import randint
from requests import get as requestsget


class TicTacToeServer:
    def __init__(self, master, conn):
        self.master = master
        self.master.title("Tic-Tac-Toe: Server Edition")
        self.conn = conn
        self.player_name = ""
        self.opponent_name = ""
        self.current_player = ""
        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        self.create_player()
        self.create_quit_button()

    def create_player(self):
        self.player_name = tk.StringVar()
        label = tk.Label(self.master, text="Enter your name:")
        label.grid(row=0, column=0)
        entry = tk.Entry(self.master, textvariable=self.player_name)
        entry.grid(row=0, column=1)

        start_button = tk.Button(self.master, text="Start Game", command = self.start_game)
        start_button.grid(row=2, columnspan=2, pady=10)

    def get_opponent(self):
        label = tk.Label(self.master, text="Waiting for opponent...")
        label.grid(row=0, column=0)
        opponent_name = self.conn.recv(1024).decode()
        if not opponent_name:
            self.master.destroy()  # TODO: handle this case properly

        label.config(text=f"Your opponent is {opponent_name}")

    def start_game(self):
        player = self.player_name.get()
        if player == "":
            messagebox.showerror("Error", "Please enter your name.")

        else:
            self.conn.send(player.encode())
            self.get_opponent()
            opponent = self.opponent_name.get()
            players = [player, opponent]
            self.current_player = players[randint(0, 1)]
            self.create_board()

    def create_board(self):
        if self.current_player == self.player_name:
            self.turn_label = tk.Label(self.master, text=f"Your turn!", font=("Arial", 14))
        else:
            self.turn_label = tk.Label(self.master, text=f"{self.opponent_name}'s turn!", font=("Arial", 14))
        self.turn_label.grid(row=3, columnspan=3)
        for i in range(3):
            for j in range(3):
                button = tk.Button(self.master, text="", width=10, height=4, fort=("Arial", 20),
                                   command=lambda row=i, col=j: self.click(row, col))
                button.grid(row=i, column=j)
                self.buttons[i][j] = button

    def create_quit_button(self):
        quit_button = tk.Button(self.master, text="Quit", command=self.master.destroy)
        quit_button.grid(row=4, columnspan=3, pady=10)

    def click(self, row, col):
        if self.board[row][col] == "":
            self.board[row][col] = self.current_player
            self.buttons[row][col].config(text=self.current_player)
            if self.check_winner(row, col):
                # TODO handle winners
                self.reset_board()
            elif self.check_draw():
                messagebox.showinfo("Tic-Tac-Toe", "It's a draw!")
                self.reset_board()
            else:
                if self.current_player == self.player_name.get():
                    self.current_player = self.opponent_name.get()
                    self.turn_label.config(text=f"{self.opponent_name}'s turn!")
                else:
                    self.current_player = self.player_name.get()
                    self.turn_label.config(test=f"Your turn!")

    def check_winner(self, row, col):
        pass # TODO

    def check_draw(self):
        return all(self.board[i][j] != "" for i in range(3) for j in range(3))

    def reset_board(self):
        self.board = [["" for _ in range(3)] for _ in range(3)]
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].config(text="")
        players = [self.player_name.get(), self.opponent_name.get()]
        self.current_player = players[randint(0, 1)]


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


def main():
    root = tk.Tk()
    host = '0.0.0.0'
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Server listening on {get_public_ip()}:{port}")
        conn, addr = s.accept()
        with conn:
            print(f"Connected to {addr}")
        app = TicTacToeServer(master=root, conn=conn)
        root.mainloop()


if __name__ == "__main__":
    main()