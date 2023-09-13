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
        self.resolve_consequences()

    def resolve_consequences(self):
        for cons in self.consequences:
            # need to implement consequences first
            cons.resolve()


class Consequence:
    def __init__(self, description: str):
        self.description = description

    def resolve(self):
        # here should happen way more complex stuff
        print(self.description)
