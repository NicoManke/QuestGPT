from pymantic import sparql


class BlazeGraph:
    def __init__(self, server_address: str):
        # server_address = ('http://192.168.2.100:9999/blazegraph/namespace/kb/sparql')
        try:
            self.server = sparql.SPARQLServer(server_address)
        except Exception as e:
            print(f"Error: {e}")
        else:
            self.server.update('LOAD <file:///D:/Bachelor/Blazegraph/files/Eich-Generated.ttl>')

    def update(self, query_string: str):
        return self.server.update(query_string)

    def query(self, query_string: str):
        return self.server.query(query_string)

    def check(self):
        result = self.server.query('''
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX ex: <http://example.org/>

            SELECT ?dragon ?location ?isAlive
            WHERE {
               ?dragon rdf:type ex:Dragon .
               ?dragon ex:isLocatedIn ?location .
               ?dragon ex:isAlive ?isAlive .
               FILTER (?isAlive = true)
               
               ex:Siegfried ex:knows ?dragon .
            }''')

        print("Dragons that are alive:")
        for b in result['results']['bindings']:
            # print(f"{b['p']['value']} | {b['o']['value']}")
            print(f"{b['dragon']['value']} | {b['location']['value']}")

        print("Kill Baldur!")
        self.server.update('''
            PREFIX ex: <http://example.org/>
            
            DELETE {
              ex:Baldur ex:isAlive ?oldValue .
            }
            WHERE {
              ex:Baldur ex:isAlive ?oldValue .
            }
            ''')

        self.server.update('''
            PREFIX ex: <http://example.org/>
            
            INSERT DATA {
                ex:Baldur ex:isAlive false .
            }
        ''')

        result = self.server.query('''
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX ex: <http://example.org/>

                    SELECT ?dragon ?location ?isAlive
                    WHERE {
                       ?dragon rdf:type ex:Dragon .
                       ?dragon ex:isLocatedIn ?location .
                       ?dragon ex:isAlive ?isAlive .
                       FILTER (?isAlive = true)

                       ex:Siegfried ex:knows ?dragon .
                    }''')

        print("Dragons that are still alive:")
        for b in result['results']['bindings']:
            # print(f"{b['p']['value']} | {b['o']['value']}")
            print(f"{b['dragon']['value']} | {b['location']['value']}")
