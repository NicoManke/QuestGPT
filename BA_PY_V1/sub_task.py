class SubTask:
    def __init__(self, name: str, description: str, type, npc, location, dialogue_options: [], consequences: []):
        self.name = name
        self.description = description
        self.type = type
        self.npc = npc
        self.location = location
        self.dialogue_opts = dialogue_options
        self.consequences = consequences
        # non structural stuff
        self.complete = False

    def __str__(self):
        return self.st_to_str()

    def st_to_str(self):
        dialogue_options_str = "\n".join([f"Dialogue_Option: {opt['DialogueID']},\nNPC: {opt['NPC']},\nDialogue: {opt['Text']}" for opt in self.dialogue_opts])
        #dialogue_options_str = "\n".join([f"Dialogue_Option: {opt.id},\nNPC: {opt.npc},\nDialogue: {opt.dialogue}" for opt in self.dialogue_opts])
        consequences_str = "\n".join([cons.description for cons in self.consequences])

        return "{" + f"Name: {self.name}\nDescription: {self.description}\nType: {self.type}\nNPC: {self.npc}\nLocation: {self.location}\n" \
               f"Dialogue Options:\n{dialogue_options_str}\nConsequences:\n{consequences_str}" + "}"

    def complete_task(self):
        self.complete = True

    def resolve_consequences(self):
        for cons in self.consequences:
            cons.resolve()


class Consequence:
    def __init__(self, description: str, update_query: str = ""):
        self.description = description
        self.__update_query = update_query

    def set_update_query(self, update_query: str):
        self.__update_query = update_query

    def get_update_query(self):
        return self.__update_query

    def resolve(self):
        # here should happen way more complex stuff
        print(self.description)
        print(self.__update_query)


class DialogueOptions:
    def __init__(self, id, previous_id, npc, dialogue):
        self.id = id
        self.prev_id = previous_id
        self.npc = npc
        self.dialogue = dialogue
