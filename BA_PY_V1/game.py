import json

import openai_facade
import quest
import consequence
import blazegraph
from utility import create_message as Message
from utility import trim_quest_structure
from utility import reorder_query_triplets
from utility import correct_query
from utility import print_response

import narrative
import quest_structure
import instructions


class Game:
    def __init__(self, api_key, api_model, max_request_tries, waiting_time, server_address):
        self.__node_messages = []
        self.__messages = []
        self.__quests = []
        self.__consequences = []
        self.__last_queried_triplets = []
        self.SYSTEM_ROLE = "system"
        self.USER_ROLE = "user"

        self.__gpt_facade = openai_facade.OpenAIFacade(api_key, api_model, max_request_tries, waiting_time=waiting_time)

        self.__server_address = server_address
        self.__bg = blazegraph.BlazeGraph(self.__server_address)

        # node graph node types here; currently just selected examples
        self.__node_types = '''
        WorldLocation, 
        Dragon, Human, Wolf, 
        Item, Weapon, Sword, WarHammer, Apparel, 
        WorldObject,
        WorldResource,
        Treasure
        '''

    def add_message(self, message: str, role: str = "user"):
        self.__messages.append(
            {"role": role,
             "content": message}
        )

    def get_response(self, response_temp=0.0):
        response = self.__gpt_facade.get_response(self.__messages, response_temp)
        self.__messages.append(response["choices"][0]["message"])
        return response

    def prompt(self):
        # add quest structure
        self.add_message(f"Here is a structure describing a quest and its attributes for a video rpg game: \n{quest_structure.get_quest_structure()}", self.SYSTEM_ROLE)
        # add narrative
        self.add_message(f"Here is the narrative of the world the game takes place in: \n{narrative.get_narrative()}", self.SYSTEM_ROLE)
        # add clear instructions
        self.add_message(instructions.get_instructions(), self.SYSTEM_ROLE)
        # make response only on request
        self.add_message(instructions.get_command(), self.SYSTEM_ROLE)

    def get_graph_knowledge(self, request: str):
        msgs = []
        query_nodes_function = [{
            "name": "query_nodes",
            "description": "Queries the nodes from a knowledge graph based on given node types.",
            "parameters": {
                "type": "object",
                "properties": {
                    "required_nodes": {
                        "type": "string",
                        "description": "An array of strings naming the node types of which instances should be queried from a knowledge graph.",
                    },
                    "required_objective": {
                        "type": "string",
                        "description": "The object or objective of the request that seems to be a name for something or someone. It should also be the name of a node, that should be queried from a knowledge graph.",
                    }
                }, "required": ["required_nodes"],
            }
        }]
        msgs.append(Message(
            f"Here is a list of all node types contained in our knowledge graph: {self.__node_types}",
            self.SYSTEM_ROLE))
        msgs.append(Message(
            f"Decide which of the given node types need to be queried based of the following user quest request: {request}",
            self.SYSTEM_ROLE))
        response = self.__gpt_facade.make_function_call(msgs, query_nodes_function, "query_nodes")

        response_message = response["choices"][0]["message"]
        # print(f"Function Call: {response_message}")
        # Step 2: check if GPT wanted to call a function
        if response_message.get("function_call"):
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            available_functions = {
                "query_nodes": self.query_nodes,
            }  # only one function in this example, but you can have multiple
            function_name = response_message["function_call"]["name"]
            function_to_call = available_functions[function_name]
            function_args = json.loads(response_message["function_call"]["arguments"])
            print(f"\nArgs: {function_args}")
            # this is the output of the actual function
            queried_nodes = function_to_call(
                required_nodes=function_args.get("required_nodes"),
                required_objective=function_args.get("required_objective"),
            )
            return queried_nodes

    def query_nodes(self, required_nodes: [], required_objective: str):
        obj_triplets = []
        node_triplets = []

        player_query_results = self.__bg.query('''
PREFIX ex: <http://example.org/>

SELECT ?node ?property ?value
WHERE {
VALUES (?node) {(ex:Stranger)}
?node ?property ?value .
}''')
        player_triplets = reorder_query_triplets(player_query_results)

        if required_objective:
            objective_query = self.generate_query_from_name(required_objective)
            obj_query_result = self.__bg.query(objective_query)
            obj_triplets = reorder_query_triplets(obj_query_result)

        # multiple tries, because the query generation tends to be not 100% valid
        try_counter = 0
        while try_counter < 3:
            response_query = self.generate_query_from_types(required_nodes)
            try_counter += 1
            try:
                query_result = self.__bg.query(response_query)
            except Exception as e:
                print(f"\nInvalid query! #Tries: {try_counter}")
                if try_counter == 3:
                    print(f"No valid was generated in {try_counter} tries!")
            else:
                print(f"\nQuery output vars: {query_result['head']['vars']}")
                # remaining code here...?
                node_triplets = reorder_query_triplets(query_result)
                break

        node_set = set(node_triplets)
        obj_set = set(obj_triplets)
        combined_set = obj_set.union(node_set)
        triplets = player_triplets + list(combined_set)
        self.__last_queried_triplets = triplets.copy()
        return triplets

    def generate_query_from_types(self, required_nodes):
        msgs = []
        node_query_request = f"You are a SparQL expert, now give me a simple SparQL query to retrieve all DISTINCT nodes, including their properties' values, of the following types and their subclasses: ({required_nodes})"
        prefixes = '''
                    Also use for this the following prefixes and include them in the query:
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX owl: <http://www.w3.org/2002/07/owl#>
                    PREFIX ex: <http://example.org/>
                '''
        only_code_command = "Only return the code of the query, nothing else, so no additional descriptions."
        msgs.append(Message(f"{node_query_request}. {prefixes}. {only_code_command}", self.SYSTEM_ROLE))

        response = self.__gpt_facade.get_response(msgs)
        response_query = correct_query(response["choices"][0]["message"]["content"])

        print(f"\nType-ish node query:\n{response_query}")

        return response_query

    def generate_query_from_name(self, required_node):
        required_node = required_node.replace(" ", "")
        response_query = '''
            PREFIX ex: <http://example.org/>

            SELECT ?node ?property ?value
            WHERE {
                ?node ?property ?value .
                FILTER (UCASE(str(?node)) = UCASE(str(ex:''' + required_node + ''')))
            }'''
        # print(f"\nName-ish node query:\n{response_query}")

        return response_query

    def generate_quest(self, quest_request: str, extracted_nodes):
        msgs = self.__messages.copy()
        msgs.append(Message(f"Take a deep breath and think about what should be part of a good rpg quest, then build the quest's story around a few of those given graph nodes extracted from the knowledge graph: {extracted_nodes}", self.USER_ROLE))
        msgs.append(Message(f"Generate a quest for the following player request, using only the given structure:\n{quest_request}", "system"))
        request_response = self.__gpt_facade.get_response(msgs, 1.0)  # self.get_response(1.0)
        generated_quest = trim_quest_structure(request_response["choices"][0]["message"]["content"])
        self.__quests.append(generated_quest)
        return generated_quest

    def correct_error(self, invalid_quest_structure: str, error_msg):
        # do call with command of "repairing" structure
        try_count = 0

        while True:
            print(f"Correction {try_count}")
            try_count += 1

            correction_msgs = self.__messages.copy()
            correction_msgs.append(Message(
                f'''In the generation of the quest structure an error occurred, see: "{error_msg}".
                    Correct the following quest structure based on the already generated content, the originally 
                    given structure, the narrative and the queried nodes. Here is the incorrect structure:
                    "{invalid_quest_structure}".
                    And here are the node triplets again: "{self.__last_queried_triplets}".
                    Additionally, check for more structural errors or missing keys and correct them.
                    ''',
                self.SYSTEM_ROLE
            ))
            response = self.__gpt_facade.get_response(correction_msgs, 0.75)
            corrected_structure = trim_quest_structure(response["choices"][0]["message"]["content"])

            try:
                json.loads(corrected_structure)
            except Exception as e:
                print(f"\nAnother Error was still found after {try_count} corrections: {e}")
                error_msg = e
                if try_count > 2:
                    break
            else:
                return corrected_structure

    def correct_structure(self, generated_quest_structure):
        counter = 0
        while True:
            try:
                json_quest = json.loads(f'{generated_quest_structure}')
            except json.JSONDecodeError as jde:
                counter += 1
                print(f"A JSON decode Error occurred. Correction-try: {counter}")
                generated_quest_structure = self.correct_error(generated_quest_structure, jde)
            except Exception as e:
                counter += 1
                print(f"The structure wasn't correctly formatted. Correction-try: {counter}")
                generated_quest_structure = self.correct_error(generated_quest_structure, e)
            else:
                break

        counter = 0
        while True:
            try:
                q_sub_tasks = json_quest["SubTasks"]
                for task in q_sub_tasks:
                    task_consequences = task["Task_Consequences"]
                    for des in task_consequences:
                        print(f"\nC.D: {des}")
                        self.create_consequence(des)
            except KeyError as ke:
                counter += 1
                print(
                    f"\nAn KeyError occurred when accessing the json-loaded quest structure:\n{ke}\nRe-try: {counter}")
                generated_quest_structure = self.correct_error(generated_quest_structure, ke)
            except Exception as e:
                counter += 1
                print(
                    f"\nAnother error occurred when accessing the json-loaded quest structure:\n{e}\nRe-try: {counter}")
                generated_quest_structure = self.correct_error(generated_quest_structure, e)
            else:
                break

        return generated_quest_structure

    def is_quest_valid(self, generated_quest_structure: str):
        # checking if there is any structure
        if generated_quest_structure.find("{") == -1 or generated_quest_structure.find("}") == -1:
            print(f"Quest wasn't generated:\n{generated_quest_structure}")
            # there is probably a new recommendation in the given answer, so it may be a good idea to re-feed the answer
            # back into the quest-generation for a 2nd round
            return False

        # counter = 0
        while True:
            try:
                json_quest = json.loads(f'{generated_quest_structure}')
            except json.JSONDecodeError as jde:
                # counter += 1
                print(f"A JSON decode Error occurred. Correction-try: ")
                return False
                # generated_quest_structure = self.correct_structure(generated_quest_structure, jde)
            except Exception as e:
                # counter += 1
                print(f"The structure wasn't correctly formatted. Correction-try: ")
                return False
                # generated_quest_structure = self.correct_structure(generated_quest_structure, e)
            else:
                break

        # counter = 0
        while True:
            try:
                q_sub_tasks = json_quest["SubTasks"]
                for task in q_sub_tasks:
                    task_consequences = task["Task_Consequences"]
                    for des in task_consequences:
                        print(f"\nC.D: {des}")
                        self.create_consequence(des)
            except KeyError as ke:
                # counter += 1
                print(f"\nAn KeyError occurred when accessing the json-loaded quest structure:\n{ke}\nRe-try: ")
                return False
                # generated_quest_structure = self.correct_structure(generated_quest_structure, ke)
            except Exception as e:
                # counter += 1
                print(f"\nAnother error occurred when accessing the json-loaded quest structure:\n{e}\nRe-try: ")
                return False
                # generated_quest_structure = self.correct_structure(generated_quest_structure, e)
            else:
                break

        validity_function = [{
            "name": "validity_check",
            "description": "Decides based on the given arguments if the quest is accepted or not.",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_quest_valid": {
                        "type": "boolean",
                        "description": "True if the generated quest is consistent with the narrative and if it is logical and playable. False if it is not.",
                    },
                    "validity_explanation": {
                        "type": "string",
                        "description": "The explanation and description of why the quest is valid or invalid.",
                    }
                }, "required": ["is_quest_valid"],
            }
        }]

        validation_msgs = self.__messages.copy()

        message = f'''Now only validate if the generated quest, as it is described in the generated structure, is 
        consistent with the narrative and the queried graph node triplets. Also make sure that it is logical and 
        playable. Here is the generated quest again:\n{generated_quest_structure}
        And here are the queried graph node triplets again:\n{self.__last_queried_triplets}'''

        validation_msgs.append(Message(message, self.SYSTEM_ROLE))
        response = self.__gpt_facade.make_function_call(validation_msgs, validity_function, "validity_check")

        response_arguments = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
        valid = response_arguments.get("is_quest_valid")
        explanation = response_arguments.get("validity_explanation")
        print(f"\nQuest Validation:\n{valid}\n{explanation}")

        #if valid:
        #    valid = self.__bg.validate_quest(generated_quest_structure) and valid

        return valid

    def clear_triplets(self):
        self.__last_queried_triplets.clear()

    def convert_quest(self, quest_structure: str):
        # something's not correct yet...
        json_quest = json.loads(f'{quest_structure}')
        # print(f"Debug JSON quest:\n{json_quest}")
        q_name = json_quest["Name"]
        q_description = json_quest["Detailed_Description"]
        q_s_description = json_quest["Short_Description"]
        q_source = json_quest["Source"]
        q_chrono = json_quest["Chronological"]
        q_sub_tasks = json_quest["SubTasks"]
        new_quest = quest.Quest(q_name, q_description, q_s_description, q_source, q_chrono, q_sub_tasks)
        return new_quest

    def create_consequence(self, description: str):
        new_cons = consequence.Consequence(description)
        self.__consequences.append(new_cons)
        return new_cons

    def update_graph(self, consequences, node_triplets):
        update_graph_msgs = self.__messages.copy()
        update_queries = []
        sparql_pattern = "DELETE {} INSERT {} WHERE {}"
        optional_block = "OPTIONAL {}"

        predicates = self.__bg.query('''
            PREFIX ex: <http://example.org/>

            SELECT DISTINCT ?predicate
            WHERE {
                ?subject ?predicate ?object
            }''')
        predicates = reorder_query_triplets(predicates)

        for cons in consequences:
            message = f'''Here is a list of RDF triplets that were taken from a knowledge graph:
            "{node_triplets}".\n
            In our RPG game, task consequences outline changes to the game world, specifically to the underlying knowledge 
            graph. Your task is to craft only one single SparQL query, based on the given triplets, that logically 
            updates the relevant triplets influenced by these consequences. Differentiate between changes that are 
            essential for the graph and those that serve purely narrative purposes. Ensure that node deletion is minimal
            , focusing on removing and changing only specific attributes when necessary. Note that the query is solely 
            intended for graph updates and does not require condition checking. Refrain from deleting entire nodes. 
            Emphasize the importance of respecting and opting for pre-existing predicates instead of introducing new 
            ones. Below is a comprehensive list of the available predicates:\n{predicates}
            Here are the task consequences:
            "{cons}".\n
            When generating the query, please use the following pattern for the query:
            "{sparql_pattern}".\n
            You may use {optional_block} inside the WHERE block if a WHERE check is really necessary, but it could be the 
            first time the triple is set.
            Also, when generating the query, please use this prefixes:
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX ex: <http://example.org/>
            '''

            update_graph_msgs.append(Message(message, self.SYSTEM_ROLE))
            response = self.__gpt_facade.get_response(update_graph_msgs)
            update_queries.append(response["choices"][0]["message"]["content"])
            usage = response["usage"]
            print(f"\nToken Info: \n{usage}")

        # instead actually update the graph...
        print(f"\nUpdate Queries:")
        i: int = 1
        for upt_query in update_queries:
            print(f"U.Q. {i}:\n{upt_query}")
            i += 1
