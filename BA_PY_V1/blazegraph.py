from pymantic import sparql


class BlazeGraph:
    def __init__(self, server_address: str, graph_file_address: str = ""):
        self.graph_file_address = graph_file_address
        try:
            self.server = sparql.SPARQLServer(server_address)
        except Exception as e:
            print(f"Graph Error: {e}")
        else:
            self.load_graph()

    def update(self, query_string: str):
        return self.server.update(query_string)

    def query(self, query_string: str):
        return self.server.query(query_string)

    def load_graph(self):
        if self.graph_file_address == "":
            print("No path was given!")
            self.server.update('LOAD <file:///D:/Bachelor/Blazegraph/files/Eich-Created.ttl>')
        elif self.graph_file_address.find(' ') != -1:
            print(f"This is an invalid path, because it contains whitespace. Your path for 'Eich-created.ttl': {self.graph_file_address}")
            self.server.update('LOAD <file:///D:/Bachelor/Blazegraph/files/Eich-Created.ttl>')
        else:
            self.server.update('LOAD <file:///' + self.graph_file_address + '>')

    def clear_graph(self):
        self.server.update("CLEAR ALL")

    def reset_graph(self):
        self.clear_graph()
        self.load_graph()


# 'D:/Bachelor/Blazegraph/files/Eich-created.ttl'
# 'http://192.168.2.100:9999/blazegraph/namespace/kb/sparql'
# self.server.update('LOAD <file:///D:/Bachelor/Blazegraph/files/Eich-Created.ttl>')
