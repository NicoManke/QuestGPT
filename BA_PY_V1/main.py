import os
import openai
import json
import quest
import knowledge_graph

node_messages = []
messages = []
quests = []

openai.api_key = os.getenv("OPENAI_API_KEY")
model = "gpt-3.5-turbo-0613"  # "gpt-4"
system_role = "system"
user_role = "user"

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
            "Description": "explaining the changes and consequences for the game world after completing the task."
        }]
    }]
}
narrative = '''
The village of Eich has 20 inhabitants. To the north of Eich lies the Blue Mountains. In the Blue Mountains, there is an 
old path that leads to a bandit camp and over a badly damaged old bridge. At the end of this path lies Dwarf Mountain, 
where the great blue dragon Smaug lives. Smaug conquered this mountain for himself many decades ago and drove away the 
dwarves who once lived there. Since then, Smaug has been considered the archenemy of all dwarves. Behind the bandit camp
, there is also a secret dungeon teeming with dangerous creatures and great treasures. Between Eich and the Blue 
Mountains are the fields of the local farmers. In the east of Eich, there are also many fields, as well as orchards. In 
the east of Eich, you will also find the Green Meadows, a habitat inhabited by thousands of free-roaming horses, cattle, 
pigs, and sheep. However, it is also home to large wolves, each as big as a stallion, which pose a great danger to 
humans as well. According to reports, a few of these wolves have been recently spotted near Eich. Some of the residents 
of Eich include Siegfried, Tom, Hector, and Markus. Siegfried is also known as the brave dragon slayer. He earned this 
title after defeating a wyvern in a distant land called Astasia, which is far to the south of Eich. Siegfried is a 
sociable fellow and always ready for the next battle against a dragon or wyvern. Tom is a farmer who tends to some of 
the northern fields and also has his own apple orchard in the east. Tom works hard and has a simple way of speaking due 
to his limited education. Recently, one of his fields in the north was burned down by Smaug. Although most of his fields 
were spared, Tom is very upset. He now fears that Smaug may target his remaining northern fields as well. Markus is a 
skilled craftsman capable of repairing various objects and structures. Perhaps Markus could repair the rickety old 
bridge in the Blue Mountains. Finally, there is Mayor Hector, who is a plump and slow-moving fellow but by no means 
mentally slow. Hector is clever and a good leader of the village of Birk. He interacts frequently with the villagers and 
is responsible for assigning new quests, even if they arise at the request of the citizens.
'''
json_structure = json.dumps(data_structure, ensure_ascii=False).replace('"', r'\"')
instructions = '''
You are now a generator of video game quests for a role-playing game. Generate the quest only in the provided JSON 
structure! Generate the quest only when you're explicitly requested to do so! Give the player the option to accept or 
decline a quest in the dialogue with an NPC. The NPC offering the quest should react according to the player's answer. 
The player character is a stranger who arrives in the village and is not identical to any of the NPCs mentioned in the 
narrative. In the quest, exclusively use NPCs, locations, items, and factions that are known to you from the given 
narrative and do not create new locations, NPCs, items, or factions! If a value is null, for example if the task doesn't 
have an NPC, then put in "null" as the value. Make sure to put the object keys of the JSON structure always in double 
quotes as described in the given JSON structure.'''
command = "From now on only generate quests if the system or the user explicitly requests you to do so!"

node_types = "Dragon, Location, Forest, Wolves"  # node graph node types here; currently just random examples


def add_message(message: str, role: str = "user"):
    messages.append(
        {"role": role,
         "content": message}
    )


def get_response(response_temp=0.0):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=response_temp,
    )
    messages.append(response["choices"][0]["message"])
    return response


def prompt():
    # add quest structure
    add_message(f"Here is a structure describing a quest for a video rpg game: \n{json_structure}", system_role)
    # add narrative
    add_message(f"Here is the narrative of the world our game takes place in: \n{narrative}", system_role)
    # add clear instructions
    add_message(instructions, system_role)
    # make response only on request
    add_message(command, system_role)


def get_graph_knowledge(request: str):
    msgs = []
    query_nodes_function = [{
        "name": "query_nodes",
        "description": "Queries the nodes from a knowledge graph based on given node types.",
        "parameters": {
            "type": "object",
            "properties": {
                "required_nodes": {
                    "type": "string",
                    "description": "An array of strings naming the node types of which instances should be queried from a knowledge graph.",
                }
            }, "required": ["required_nodes"],
        }
    }]

    msgs.append(
        {"role": system_role,
         "content":
             f"Here is a list of all node types contained in our knowledge graph: {node_types}"}
    )
    msgs.append(
        {"role": system_role,
         "content":
             f"Decide which of the given node types need to be queried based of the following user request: {request}"}
    )

    response = openai.ChatCompletion.create(
        model=model,
        messages=msgs,
        functions=query_nodes_function,
        function_call={"name": "query_nodes"},
    )
    response_message = response["choices"][0]["message"]
    print(f"Function Call: {response_message}")

    # Step 2: check if GPT wanted to call a function
    if response_message.get("function_call"):
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "query_nodes": query_nodes,
        }  # only one function in this example, but you can have multiple
        function_name = response_message["function_call"]["name"]
        function_to_call = available_functions[function_name]
        function_args = json.loads(response_message["function_call"]["arguments"])
        print(f"Args: {function_args}")
        # this is the output of the actual function
        queried_nodes = function_to_call(
            required_nodes=function_args.get("required_nodes"),
        )

        ## OPTIONAL!!
        ## Step 4: send the info on the function call and function response to GPT
        #msgs.append(response_message)  # extend conversation with assistant's reply
        #msgs.append(
        #    {
        #        "role": "function",
        #        "name": function_name,
        #        # output of the actual function gets fed back to generate a response in natural language
        #        "content": f"Here are the queried nodes: {queried_nodes}",
        #    }
        #)
        ## here an additional message could be integrated/added
        #second_response = openai.ChatCompletion.create(
        #    model=model,
        #    messages=msgs,
        #)  # get a new response from GPT where it can see the function response
        #
        #return second_response
        return queried_nodes


def query_nodes(required_nodes: []):
    # do multiple KG API queries to get all required nodes
    # ...
    # let's say the player asks for a dragon fight, then "Smaug" or his identifier should be part of the queries output. But which data type?
    # How should the Node output look like or how DOES it look like?
    # ["", ""] seems not to work... -> dictionary or json.loads(...) ?!
    return ["Smaug"]


def generate_quest(quest_request: str, extracted_nodes):
    add_message(f"Build the quest's story around these given graph nodes extracted from the narrative: {extracted_nodes}")
    add_message(f"Generate a quest for the following player request, using only the given structure:\n{quest_request}", "system")
    request_response = get_response(1.0)
    generated_quest = request_response["choices"][0]["message"]["content"]
    quests.append(generated_quest)
    return generated_quest


def convert_quest(quest_structure: str):
    # something's not correct yet...
    json_quest = json.loads(f'{quest_structure}')
    q_name = json_quest["Name"]
    q_description = json_quest["Detailed_Description"]
    q_s_description = json_quest["Short_Description"]
    q_source = json_quest["Source"]
    q_chrono = json_quest["Chronological"]
    q_sub_tasks = json_quest["SubTasks"]
    new_quest = quest.Quest(q_name, q_description, q_s_description, q_source, q_chrono, q_sub_tasks)
    return new_quest


def main():
    # gives the LLM the prompt (narrative, structure, instructions, etc.):
    prompt()
    first_response = get_response()
    print(first_response["choices"][0]["message"]["content"])
    # get user request:
    user_request = input("Please tell us what quest you want to play.")
    # -> I want to explore a dungeon.
    # -> I want to kill a dragon.
    # get knowledge from graph:
    extracted_nodes = get_graph_knowledge(user_request)
    print(f"Extracted Nodes: {extracted_nodes}\n")

    gen_quest = generate_quest(user_request, extracted_nodes)
    # validate generated quest:
    kg = knowledge_graph.KnowledgeGraph("42")
    if kg.validate_quest(gen_quest):
        print(gen_quest)
        # translate generated quest into an actual playable quest:
        gen = convert_quest(gen_quest)  # conversion into an quest object functions (if key values have double quotes)
        # gen.debug_quest()
    else:
        print("Retry!")
        # retry


if __name__ == '__main__':
    main()


# def run_conversation(user_request):
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
