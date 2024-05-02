from src.engine import play_game
from curses import wrapper

def main(stdscr) -> None:
    play_game(stdscr)

if __name__ == "__main__":
    wrapper(main)