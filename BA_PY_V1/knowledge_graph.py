class KnowledgeGraph:
    def __init__(self, key: str):
        #print("Who let the dogs out!")
        # access graph/stardog
        self.key = key

    def get_node(self, node_id: str):
        print(node_id)

    def update_graph(self, new_knowledge: str):
        print(new_knowledge)

    def validate_quest(self, quest):
        #print("Validation!")
        # ask LLM?
        # check if nodes are accessible?
        if True:
            return True
        else:
            return False


