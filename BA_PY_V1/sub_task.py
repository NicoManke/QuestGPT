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

    def complete_task(self):
        self.complete = True
        #self.resolve_consequences()

    def resolve_consequences(self):
        for cons in self.consequences:
            # need to implement consequences first
            cons.resolve()


class Consequence:
    def __init__(self, description: str, update_query: str = ""):
        self.description = description
        self.update_query = update_query

    def resolve(self):
        # here should happen way more complex stuff
        print(self.description)
        print(self.update_query)


class DialogueOptions:
    def __init__(self, id, previous_id, npc, dialogue):
        self.id = id
        self.prev_id = previous_id
        self.npc = npc
        self.dialogue = dialogue
