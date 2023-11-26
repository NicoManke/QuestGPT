import os
import game


def main():

    game_instance = game.Game(
        os.getenv("OPENAI_API_KEY"),
        "gpt-4",
        12,
        10,
        os.getenv("Blazegraph_Address"),
        os.getenv("Graph_File")
    )

    game_instance.run()


if __name__ == '__main__':
    main()
