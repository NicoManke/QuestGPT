from pymantic import sparql


class BlazeGraph:
    def __init__(self, server_address: str):
        # server_address = ('http://192.168.2.100:9999/blazegraph/namespace/kb/sparql')
        self.server = sparql.SPARQLServer(server_address)

    def update(self, query_string: str):
        self.server.update(query_string)

    def query(self, query_string: str):
        self.server.query(query_string)

    def check(self):
        self.server.update('LOAD <file:///D:/Bachelor/Blazegraph/files/foaf-bond.ttl>')

        result = self.server.query('select * where { <http://blazegraph.com/blazegraph> ?p ?o }')
        for b in result['results']['bindings']:
            print(f"{b['p']['value']} | {b['o']['value']}")
