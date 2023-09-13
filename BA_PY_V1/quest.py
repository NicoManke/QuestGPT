import sub_task


class Quest:
    def __init__(self, name: str, description: str, short_description: str, source, chronological: bool, sub_tasks: []):
        self.name = name
        self.description = description
        self.short_desc = short_description
        self.source = source
        self.chrono = chronological
        self.sub_tasks = sub_tasks

    def add_task(self, task: sub_task.SubTask):
        if isinstance(task, sub_task.SubTask):
            self.sub_tasks.append(task)
        else:
            raise TypeError("Only SubTask objects can be added to the list")

    def debug_quest(self):
        print(f"Name: {self.name}")
        print(f"Desc: {self.description}")
        print(f"Chro: {self.chrono}, {type(self.chrono)}")
