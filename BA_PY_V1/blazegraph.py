from pymantic import sparql


class BlazeGraph:
    def __init__(self):
        # server = sparql.SPARQLServer('http://127.0.0.1:9999/bigdata/sparql')
        self.server = sparql.SPARQLServer('http://192.168.2.100//:9999/blazegraph/kb/sparql')

        # Loading data to Blazegraph
        # server.update('load <file:///tmp/data.n3>')
        self.server.update('load <D:/Code Projects/Bachelor_Blazegraph_Test/Test1/foaf-bond.ttl>')

        # Executing query
        result = self.server.query('select * where { <http://blazegraph.com/blazegraph> ?p ?o }')
        for b in result['results']['bindings']:
            print(f"{b['p']['value']} | {b['o']['value']}")
            # print("%s %s" (b['p']['value'], b['o']['value']))
