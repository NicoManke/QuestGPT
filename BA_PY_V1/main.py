import os
import game
from utility import print_response


def main():
    game_instance = game.Game(
        os.getenv("OPENAI_API_KEY"),
        "gpt-4",
        12,
        10,
        'http://192.168.2.100:9999/blazegraph/namespace/kb/sparql'
    )

    # game loop
    game_instance.run()


if __name__ == '__main__':
    main()
