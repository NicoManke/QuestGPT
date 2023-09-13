import os
import openai
import json
import narrative
import quest

messages = []
quests = []

openai.api_key = os.getenv("OPENAI_API_KEY")
model = "gpt-3.5-turbo-0613"
system_role = "system"

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
            # responses? this way?
            #"Response": "the player's possible responses",
            "DialogueID": "the dialogue\'s ID, like d_n, where d stands for dialogue and n is the unique number.",
            "PreviousDialog": "the ID of the previous dialogue that had to be played."
        }],
        "Task_Consequences": [{
            "Description": "explaining the changes and consequences for the game world"
        }]
    }]
}
json_structure = json.dumps(data_structure, ensure_ascii=False).replace('"', r'\"')
instructions = '''
You are now a generator of video game quests for a role-playing game. Generate the quest only in the provided JSON 
structure! Generate the quest only when you're explicitly requested to do so! Give the player the option to accept or 
decline a quest in the dialogue with an NPC. The NPC offering the quest should react according to the player's answer. 
The player character is a stranger who arrives in the village and is not identical to any of the NPCs mentioned in the 
narrative. In the quest, exclusively use NPCs, locations, items, and factions that are known to you from the given 
narrative and do not create new locations, NPCs, items, or factions! If a value is null, for example if the task doesn't 
have an NPC, then put in "null" as the value. Make sure to put the object keys of the JSON structure always in double 
quotes as described in the given JSON structure'''
command = "From now on only generate quests if the system or the user explicitly requests you to do so!"


def prompt():
    # add quest structure
    add_message(f"Here is a structure describing a quest for a video rpg game: \n{json_structure}", system_role)
    # add narrative
    add_message(f"Here is the narrative of the world our game takes place in: \n{narrative}", system_role)
    # add clear instructions
    add_message(instructions, system_role)
    # make response only on request
    add_message(command, system_role)


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


def generate_quest(quest_request: str):
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


if __name__ == '__main__':
    # gives the LLM the prompt (narrative, structure, instructions, etc.):
    prompt()
    first_response = get_response()
    print(first_response["choices"][0]["message"]["content"])
    # get user request:
    user_request = input("Please tell us what quest you want to play.")
    # -> I want to explore a dungeon.
    # -> I want to kill a dragon.
    # get knowledge from graph:
    # ...
    gen_quest = generate_quest(user_request)
    # validate generated quest:
    # ...
    print(gen_quest)
    # translate generated quest into an actual playable quest:
    gen = convert_quest(gen_quest) # conversion into an quest object functions (if key values have double quotes)
    #gen.debug_quest()

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
