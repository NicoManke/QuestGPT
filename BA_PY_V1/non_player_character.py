class NPC:
    def __init__(self, npc_id: str, npc_name: str, dialogue_options: []):
        self.npc_id = npc_id
        self.name = npc_name
        self.dialogue_options = dialogue_options


class DialogueOption:
    def __init__(self, dialogue_id: str, prev_dialogue_id: str, dialogue_text: str, dialogue_response: str):
        self.d_id = dialogue_id
        self.prev_d_id = prev_dialogue_id
        self.text = dialogue_text
        self.response = dialogue_response

