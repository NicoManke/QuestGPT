import os
import openai
import json

messages = []
quests = []

openai.api_key = os.getenv("OPENAI_API_KEY")
model = "gpt-3.5-turbo-0613"

data_structure = {
    "Name": "name of quest",
    "Detailed_Description": "More detailed description explaining exactly what is supposed to happen in the quest.",
    "Short_Description": "short describing text for the quest that reflects its overall goal",
    "Source": "the initial source of the quest. Can be an NPC or a quest board, if available",
    "Chronological": "bool that defines if the sub tasks have to be done in a chronological order or not.",
    "SubTasks": [{
        "Name": "name of the sub task",
        "Description": "description of what needs to be done to complete the sub task",
        "Type": "enum kill, hunt, catch, explore",
        "NPC": "name of NPC connected to the subtask",
        "Location": "name of the location the task takes place",
        "DialogueOptions": [{
            "NPC": "name of NPC",
            "Text": "text",
            "DialogueID": "the dialogue\'s ID, like d_n, where d stands for dialogue and n is the unique number.",
            "PreviousDialog": "the ID of the previous dialogue that had to be played."
        }],
        "Task_Consequences": [{
            "Description": "explaining the changes and consequences for the game world"
        }]
    }]
}
json_structure = json.dumps(data_structure, ensure_ascii=False).replace('"', r'\"')
narrative = '''The village of Eich has 20 inhabitants. To the north of Eich lies the Blue Mountains. In the Blue Mountains, there is an old path that leads to a bandit camp and over a badly damaged old bridge. At the end of this path lies Dwarf Mountain, where the great blue dragon Smaug lives. Smaug conquered this mountain for himself many decades ago and drove away the dwarves who once lived there. Since then, Smaug has been considered the archenemy of all dwarves. Behind the bandit camp, there is also a secret dungeon teeming with dangerous creatures and great treasures. Between Eich and the Blue Mountains are the fields of the local farmers. In the east of Eich, there are also many fields, as well as orchards. In the east of Eich, you will also find the Green Meadows, a habitat inhabited by thousands of free-roaming horses, cattle, pigs, and sheep. However, it is also home to large wolves, each as big as a stallion, which pose a great danger to humans as well. According to reports, a few of these wolves have been recently spotted near Eich. Some of the residents of Eich include Siegfried, Tom, Hector, and Markus. Siegfried is also known as the brave dragon slayer. He earned this title after defeating a wyvern in a distant land called Astasia, which is far to the south of Eich. Siegfried is a sociable fellow and always ready for the next battle against a dragon or wyvern. Tom is a farmer who tends to some of the northern fields and also has his own apple orchard in the east. Tom works hard and has a simple way of speaking due to his limited education. Recently, one of his fields in the north was burned down by Smaug. Although most of his fields were spared, Tom is very upset. He now fears that Smaug may target his remaining northern fields as well. Markus is a skilled craftsman capable of repairing various objects and structures. Perhaps Markus could repair the rickety old bridge in the Blue Mountains. Finally, there is Mayor Hector, who is a plump and slow-moving fellow but by no means mentally slow. Hector is clever and a good leader of the village of Birk. He interacts frequently with the villagers and is responsible for assigning new quests, even if they arise at the request of the citizens.'''
instructions = '''You are now a generator of video game quests for a role-playing game. Generate the quest only in the provided JSON structure and only when explicitly requested to do so. Always give the player the option to accept or decline a quest in the dialogue. The NPC offering the quest should react according to the player's answer. The player character is a stranger who arrives in the village and is not identical to any of the NPCs mentioned in the narrative. In the quest, exclusively use NPCs, locations, items, and factions that are known to you from the given narrative. Do not create new locations, NPCs, items, or factions.'''
command = "From now on only generate quests if the system or the user explicitly requests you to do so!"


def prompt():
    # add quest structure
    add_message(f"Here is a structure describing a quest for a video rpg game: \n{json_structure}", "system")
    # add narrative
    add_message(f"Here is the narrative of the world our game takes place in: \n{narrative}", "system")
    # add clear instructions
    add_message(instructions, "system")
    # make response only on request
    add_message(command, "system")


def add_message(message: str, role: str = "user"):
    messages.append(
        {"role": role,
         "content": message}
    )


def get_response():
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
    )
    messages.append(response["choices"][0]["message"])
    return response


def generate_quest(quest_request: str):
    add_message(f"Generate a quest for the following player request:\n{quest_request}", "system")
    request_response = get_response()
    quest = request_response["choices"][0]["message"]["content"]
    quests.append(quest)
    return quest


if __name__ == '__main__':
    # gives the LLM the prompt (narrative, structure, instructions, etc.):
    prompt()
    first_response = get_response()
    print(first_response["choices"][0]["message"]["content"])
    # get user request:
    user_request = input("Please tell us what quest you want to play.")
    # get knowledge from graph:
    # ...
    gen_quest = generate_quest(user_request)
    # validate generated quest:
    # ...
    print(gen_quest)
    # translate generated quest into an actual playable quest:
    # ...



#def run_conversation(user_request):
#    # Step 1: send the conversation and available functions to GPT
#    messages.append(
#        {"role": "user",
#         "content": "The player wants a new quest. Here is his request for the new quest: " + user_request}
#    )
#    functions = [
#        {
#            "name": "generate_quest",
#            "description": "Generates a story coherent quest for our RPG game.",
#            "parameters": {
#                "type": "object",
#                "properties": {
#                    "node_id": {
#                        "type": "string",
#                        "description": "The identification number of the start node in the knowledge graph",
#                    },
#                    "quest_type": {
#                        "type": "string",
#                        "enum": ["kill", "catch", "collect"],
#                        "description": "Defines the type of the task that has to be done in the quest.",
#                    },
#                },
#                "required": ["node_id", "quest_type"],
#            },
#        }
#    ]
#
#    response = openai.ChatCompletion.create(
#        model=model,
#        messages=messages,
#        functions=functions,
#        function_call="auto",
#    )
#
#    response_message = response["choices"][0]["message"]
#    print(response_message.content)
#
#    # Step 2: check if GPT wanted to call a function
#    if response_message.get("function_call"):
#        # Step 3: call the function
#        # Note: the JSON response may not always be valid; be sure to handle errors
#        available_functions = {
#            "generate_quest": generate_quest,
#        }  # only one function in this example, but you can have multiple
#        function_name = response_message["function_call"]["name"]
#        function_to_call = available_functions[function_name]
#        function_args = json.loads(response_message["function_call"]["arguments"])
#        # this is the output of the actual function
#        function_response = function_to_call(
#            node_id=function_args.get("node_id"),
#            quest_type=function_args.get("quest_type"),
#        )
#
#        # Step 4: send the info on the function call and function response to GPT
#        messages.append(response_message)  # extend conversation with assistant's reply
#        messages.append(
#            {
#                "role": "function",
#                "name": function_name,
#                # output of the actual function gets fed back to generate a response in natural language
#                "content": function_response,
#            }
#        )
#        # here an additional message could be integrated/added
#        second_response = openai.ChatCompletion.create(
#            model=model,
#            messages=messages,
#        )  # get a new response from GPT where it can see the function response
#
#        return second_response
