class ColorConsole:
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    def __init__(self, game_name: str = "Game", do_debug: bool = True):
        self.__game_name = game_name
        self.__do_debug = do_debug

    def coco_error(self, text: str):
        print(f"{self.RED}ERROR:{self.RESET} {text}")

    def coco_debug(self, text: str):
        if self.__do_debug:
            print(f"{self.BRIGHT_GREEN}Debug:{self.RESET}{self.BRIGHT_BLACK} {text}{self.RESET}")

    def coco_print(self, text: str):
        print(f"{self.YELLOW}System:{self.RESET} {text}")

    def coco_game(self, text: str):
        print(f"{self.MAGENTA}{self.__game_name}:{self.RESET} {text}")

    def coco_input(self, text: str):
        return input(f"{self.MAGENTA}{self.__game_name}:{self.RESET} {text}\n{self.CYAN}Input:{self.RESET} ")


