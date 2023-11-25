import os
import game


def main():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(this_dir, "Eich-created.ttl")

    game_instance = game.Game(
        os.getenv("OPENAI_API_KEY"),
        "gpt-4",
        12,
        10,
        os.getenv("Blazegraph_Address"),
        file_path
    )

    game_instance.run()


if __name__ == '__main__':
    main()
