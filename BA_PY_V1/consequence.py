class Consequence:
    def __init__(self, description: str):
        self.description = description

    def trigger(self):
        print(f"Cons:\n{self.description}")
