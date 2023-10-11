class Consequence:
    def __init__(self, description: str, cons_type="", object_reference="", parameter="", new_value=""):
        self.description = description
        self.cons_type = cons_type
        self.object_ref = object_reference
        self.parameter = parameter
        self.new_value = new_value

    def trigger(self):
        # change parameter of object_reference to new_value
        print(f"Cons. is triggered:\n{self.cons_type}, {self.object_ref}, {self.parameter}, {self.new_value}, \n{self.description}")
