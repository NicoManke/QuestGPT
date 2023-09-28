import json


def get_quest_structure():
    data_structure = {
        "Name": "name of the quest",
        "Detailed_Description": "More detailed description explaining exactly what is supposed to happen in the quest.",
        "Short_Description": "shorter version of the Detailed_Description for the quest that reflects its overall goal",
        "Source": "the initial source of the quest. Can be an NPC or a quest board, if available",
        "Chronological": "bool that defines if the sub tasks have to be done in a chronological order or not.",
        "SubTasks": [{
            "Name": "name of the sub task",
            "Description": "detailed description of what needs to be done to complete the sub task",
            "Type": "an enum with the following values: kill, hunt, catch, explore, craft, dialogue",
            "NPC": "name of the NPC connected to the subtask",
            "Location": "name of the location the task takes place at",
            "DialogueOptions": [{
                "NPC": "name of the NPC that talks to the player or the player himself, if it's his own dialogue",
                "Text": "the spoken dialogue either starting the conversation or following the previous dialogue",
                "DialogueID": "the dialogue's ID, like d_n, where d stands for dialogue and n is the unique number.",
                "PreviousDialog": "the ID of the previous dialogue that had to be played before arriving at this dialogue."
            }],
            "Task_Consequences": [{
                "Description": '''Description of the changes to the game world that are the results of the player's 
                actions during the task. For example if the player kills an NPC this NPC's property "isAlive" may be 
                changed to false and other NPCs may be informed about said death.'''
                # explaining the changes and consequences for the game world after completing the task.
            }]
        }]
    }
    json_structure = json.dumps(data_structure, ensure_ascii=False).replace('"', r'\"')

    return json_structure
