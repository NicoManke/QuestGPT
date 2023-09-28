import blazegraph
import game


def main():
    game_instance = game.Game()
    bg = blazegraph.BlazeGraph(game_instance.server_address)

    game_instance.prompt()
    first_response = game_instance.get_response()
    game_instance.print_response(first_response)

    user_request = input("Please tell us what quest you want to play.")

    extracted_nodes = game_instance.get_graph_knowledge(user_request)

    gen_quest = game_instance.generate_quest(user_request, extracted_nodes)

    if game_instance.is_quest_valid(gen_quest):
        gen = game_instance.convert_quest(gen_quest)
    else:
        print("The Quest wasn't valid, please try again.")


if __name__ == '__main__':
    main()
