import json


def get_quest_structure():
    data_structure = {
        "Name": "name of the quest",
        "Detailed_Description": "Detailed description explaining exactly what is supposed to happen in the quest.",
        "Short_Description": "shorter version of the Detailed_Description for the quest that reflects its overall goal",
        "Source": "the initial source of the quest. Can be an NPC or, if available, a quest board",
        "Chronological": "bool that defines based on the quest's story if the sub tasks have to be completed in a chronological order or not.",
        "SubTasks": [{
            "Name": "name of the sub task",
            "Description": "detailed description of what needs to be done to complete the sub task",
            "Type": "an enum with the following values: kill, hunt, catch, explore, craft, dialogue",
            "NPC": "name of the NPC connected to the subtask",
            "Location": "name of the location the task takes place at",
            "DialogueOptions": [{
                "NPC": "name of the NPC, that talks to the player, or the player himself, if it is his own dialogue",
                "Text": "the spoken dialogue, either starting the conversation or following the previous dialogue",
                "DialogueID": "the dialogue's ID, like d_n, where d stands for dialogue and n is the unique number.",
                "PreviousDialog": "the ID of the previous dialogue that had to be played before arriving at this dialogue."
            }],
            "Task_Consequences": [{
                "Description": '''
                Provide short descriptive sentences for the changes to the game world and the Knowledge Graph resulting 
                from the player's actions during the task. Use the parameter "description" to detail the alterations in 
                properties, states, or relationships of nodes in the graph. To learn about already existing properties
                , states and relationships see the provided triplets and base the changes off of them.
                For example, if the player kills an NPC, specify that the NPC's property "isAlive" should be changed to 
                false. Additionally, mention any consequences, such as other NPCs being informed about the death. If the 
                task involves repairing a structure like an old bridge, describe the changes, like updating the bridge's 
                status from damaged to repaired or fully functional.
                Ensure each "description" provides a clear and concise explanation of the impact on the game world and 
                the Knowledge Graph. This information will be used to dynamically update the state of the virtual 
                environment based on the player's choices.
                '''
            }]
        }]
    }
    json_structure = json.dumps(data_structure, ensure_ascii=False).replace('"', r'\"')

    return json_structure
