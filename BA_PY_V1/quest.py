import sub_task


class Quest:
    def __init__(self, name: str, description: str, short_description: str, source, chronological: bool, sub_tasks: [], strucutre: str):
        self.name = name
        self.description = description
        self.short_desc = short_description
        self.source = source
        self.chrono = chronological
        self.sub_tasks = sub_tasks
        self.__origin_structure = strucutre

    def __str__(self):
        return self.__origin_structure

    def to_string(self):
        return self.__origin_structure

    def to_str(self):
        sub_tasks_str = ""
        for st in self.sub_tasks:
            sub_tasks_str = f"{sub_tasks_str}{st.st_to_str()}, "
        as_string = "{ " + f"Name: {self.name}, Description: {self.description}, Source: {self.source}, Sub Tasks: [{sub_tasks_str}]" + " }"
        return as_string

    def add_task(self, task: sub_task.SubTask):
        if isinstance(task, sub_task.SubTask):
            self.sub_tasks.append(task)
        else:
            raise TypeError("Only SubTask objects can be added to the list")

    def debug_quest(self):
        print(f"Name: {self.name}")
        print(f"Desc: {self.description}")
        print(f"Chro: {self.chrono}, {type(self.chrono)}")
