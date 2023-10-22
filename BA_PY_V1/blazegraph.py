from pymantic import sparql


class BlazeGraph:
    def __init__(self, server_address: str):
        # server_address = ('http://192.168.2.100:9999/blazegraph/namespace/kb/sparql')
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
        self.server.update('LOAD <file:///D:/Bachelor/Blazegraph/files/Eich-Created.ttl>')

    def clear_graph(self):
        self.server.update("CLEAR ALL")

    def reset_graph(self):
        self.clear_graph()
        self.load_graph()

    def validate_quest(self, quest):
        return True
