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

    game_instance.prompt()
    first_response = game_instance.get_response()
    print_response(first_response)

    print('''\nWelcome to the town of Eich wandering loner! You may now call this your new home. Help the villagers, explore the world and seek new challenges in form of quests.''')

    user_request = input("\nPlease tell us what quest you want to play.")

    extracted_nodes = game_instance.get_graph_knowledge(user_request)

    gen_quest = game_instance.generate_quest(user_request, extracted_nodes)

    gen_quest = game_instance.correct_structure(gen_quest)

    if game_instance.is_quest_valid(gen_quest):
        gen = game_instance.convert_quest(gen_quest)
    else:
        print("\nGenerated quest was not valid.")
        # gen = game_instance.convert_quest()

    game_instance.clear_triplets()

    # update graph
    consequences = []
    for st in gen.sub_tasks:
        for cons in st["Task_Consequences"]:
            consequences.append(cons["Description"])
    game_instance.update_graph(consequences, extracted_nodes)


if __name__ == '__main__':
    main()
