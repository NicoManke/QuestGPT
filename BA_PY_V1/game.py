import openai
import json

import quest
import consequence
import blazegraph
import utility

import narrative
import quest_structure
import instructions


class Game:
    def __init__(self, api_key, api_model, server_address):
        self.__node_messages = []
        self.__messages = []
        self.__quests = []
        self.__consequences = []
        self.SYSTEM_ROLE = "system"
        self.USER_ROLE = "user"

        openai.api_key = api_key
        self.__model = api_model  # "gpt-3.5-turbo-0613" or "gpt-4"
        self.__server_address = server_address
        self.__bg = blazegraph.BlazeGraph(self.__server_address)

        # node graph node types here; currently just selected examples
        self.__node_types = '''
        WorldLocation, 
        Dragon, Human, Wolf, 
        Item, Weapon, Sword, WarHammer, Apparel, 
        WorldObject,
        WorldResource
        '''

    def get_server_address(self):
        return self.__server_address

    def add_message(self, message: str, role: str = "user"):
        self.__messages.append(
            {"role": role,
             "content": message}
        )

    def get_response(self, response_temp=0.0):
        response = openai.ChatCompletion.create(
            model=self.__model,
            messages=self.__messages,
            temperature=response_temp,
        )
        self.__messages.append(response["choices"][0]["message"])
        return response

    def print_response(self, response):
        print(response["choices"][0]["message"]["content"])

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
        msgs.append(
            {"role": self.SYSTEM_ROLE,
             "content":
                 f"Here is a list of all node types contained in our knowledge graph: {self.__node_types}"}
        )
        msgs.append(
            {"role": self.SYSTEM_ROLE,
             "content":
                 f"Decide which of the given node types need to be queried based of the following user quest request: {request}"}
        )
        response = openai.ChatCompletion.create(
            model=self.__model,
            messages=msgs,
            functions=query_nodes_function,
            function_call={"name": "query_nodes"},
        )
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
            print(f"Args: {function_args}")
            # this is the output of the actual function
            queried_nodes = function_to_call(
                required_nodes=function_args.get("required_nodes"),
                required_objective=function_args.get("required_objective"),
            )
            return queried_nodes

    def query_nodes(self, required_nodes: [], required_objective: str):
        # bg = blazegraph.BlazeGraph(self.__server_address)
        try_counter = 0
        obj_triplets = []
        node_triplets = []

        if required_objective:
            objective_query = self.generate_query_from_name(required_objective)
            obj_query_result = self.__bg.query(objective_query)
            obj_triplets = utility.reorder_query_triplets(obj_query_result)

        # multiple tries, because the query generation tends to be not 100% valid
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
                print(f"\nQuery output vars:\n{query_result['head']['vars']}")
                # remaining code here...?
                node_triplets = utility.reorder_query_triplets(query_result)
                break

        triplets = obj_triplets + node_triplets
        return triplets

    def generate_query_from_types(self, required_nodes):
        msgs = []
        node_query_request = f"Give me a simple SparQL query to retrieve all nodes, including their properties' values, of the following types and their subclasses: ({required_nodes})"
        prefixes = '''
                    Also use for this the following prefixes and include them in the query:
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX owl: <http://www.w3.org/2002/07/owl#>
                    PREFIX ex: <http://example.org/>
                '''
        only_code_command = "Only return the code of the query, nothing else, so no additional descriptions."
        msgs.append(
            {"role": self.SYSTEM_ROLE,
             "content": f"{node_query_request}. {prefixes}. {only_code_command}"}
        )
        response = openai.ChatCompletion.create(
            model=self.__model,
            messages=msgs
        )
        response_query = utility.correct_query(response["choices"][0]["message"]["content"])

        print(f"\nType-ish node query:\n{response_query}")

        return response_query

    def generate_query_from_name(self, required_node):
        required_node = required_node.replace(" ", "")
        head_part = '''
            PREFIX ex: <http://example.org/>

            SELECT ?node ?property ?value
            WHERE {'''
        # where_part = f"ex:{required_node} ?property ?value ."
        where_part = "VALUES (?node) {(ex:" + required_node + ")}"
        closing_bracket = "?node ?property ?value . }"
        response_query = f"{head_part}{where_part}{closing_bracket}"
#
        print(f"\nName-ish node query:\n{response_query}")

        return response_query

    def generate_quest(self, quest_request: str, extracted_nodes):
        self.add_message(f"Build the quest's story around a few of these given graph nodes extracted from the knowledge graph: {extracted_nodes}")
        self.add_message(f"Generate a quest for the following player request, using only the given structure:\n{quest_request}", "system")
        request_response = self.get_response(1.0)
        generated_quest = utility.trim_quest_structure(request_response["choices"][0]["message"]["content"])
        self.__quests.append(generated_quest)
        return generated_quest

    def correct_structure(self, invalid_quest_structure: str, error_msg):
        # do call with command of "repairing" structure
        try_count = 0

        while True:
            print(f"Correction {try_count}")
            try_count += 1

            print(f"An KeyError occurred when accessing the json-loaded quest structure: {error_msg}")
            correction_msgs = self.__messages.copy()
            correction_msgs.append(
                {"role": self.SYSTEM_ROLE,
                 "content": f'''In the generation of the quest structure an error occurred. Here is the error: "{error_msg}".
                             Please correct the following quest structure based on the already generated content, the originally 
                             given structure, the narrative and the queried nodes. Here is the incorrectly generated structure:
                             "{invalid_quest_structure}".
                             Additionally, check for more structural errors or missing keys and correct them together with the 
                             provided error.
                             '''}
            )
            response = openai.ChatCompletion.create(
                model=self.__model,
                messages=correction_msgs,
            )
            corrected_structure = utility.trim_quest_structure(response["choices"][0]["message"]["content"])

            try:
                loaded_corrected_structure = json.loads(corrected_structure)
            except Exception as e:
                print(f"Error: {e}")
                if try_count > 2:
                    break
            else:
                return loaded_corrected_structure

    def is_quest_valid(self, generated_quest_structure: str):
        # checking if there is any structure
        if generated_quest_structure.find("{") == -1 or generated_quest_structure.find("}") == -1:
            print(f"Quest wasn't generated:\n{generated_quest_structure}")
            # there is probably a new recommendation in the given answer, so it may be a good idea to re-feed the answer
            # back into the quest-generation for a 2nd round
            return False

        try:
            json_quest = json.loads(f'{generated_quest_structure}')
        except Exception as e:
            print("The structure wasn't correctly formatted. (Maybe try correcting the structure...")
            print(f"See the error message:\n{e}")
            return False

        try:
            q_sub_tasks = json_quest["SubTasks"]
            for task in q_sub_tasks:
                task_consequences = task["Task_Consequences"]
                for des in task_consequences:
                    print(f"\nC.D: {des}")
                    self.create_consequence(des)
        except KeyError as ke:
            print(f"An KeyError occurred when accessing the json-loaded quest structure: {ke}")
            generated_quest_structure = self.correct_structure(generated_quest_structure, ke)
            # still misses conversion of task_consequences
        except Exception as e:
            print(f"Another error occurred when accessing the json-loaded quest structure: {e}")
            generated_quest_structure = self.correct_structure(generated_quest_structure, e)
            # still misses conversion of task_consequences

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

        # separate copy of the original conversation
        validation_msgs = self.__messages.copy()

        message = f'''Now only validate if the generated quest, as it is described in the generated structure, is 
        consistent with the narrative and if it is logical and playable. Here is the generated quest again:
        \n{generated_quest_structure}'''

        validation_msgs.append(
            {"role": self.SYSTEM_ROLE,
             "content": message}
        )
        response = openai.ChatCompletion.create(
            model=self.__model,
            messages=validation_msgs,
            functions=validity_function,
            function_call={"name": "validity_check"},
        )

        response_arguments = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
        args = response_arguments.get("is_quest_valid")
        print(f"Args:\n{response_arguments}")
        valid = args

        if valid:
            bg = blazegraph.BlazeGraph(self.__server_address)
            valid = bg.validate_quest(generated_quest_structure) and valid

        return valid

    def convert_quest(self, quest_structure: str):
        # something's not correct yet...
        json_quest = json.loads(f'{quest_structure}')
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

        for cons in consequences:
            message = f'''Here is a list of RDF triplets that were taken from a knowledge graph:
            "{node_triplets}".\n
            In our RPG game, task consequences outline changes to the game world, specifically to the underlying knowledge 
            graph. Your task is to craft only one single SparQL query that logically updates the relevant triplets 
            influenced by these consequences. Differentiate between changes that are essential for the graph and those that 
            serve purely narrative purposes. Ensure that node deletion is minimal, focusing on removing and changing only 
            specific attributes when necessary. Note that the query is solely intended for graph updates and does not 
            require condition checking. Refrain from deleting entire nodes. 
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
            PREFIX schema: <https://schema.org/>
            PREFIX ex: <http://example.org/>
            '''

            update_graph_msgs.append(
                {"role": self.SYSTEM_ROLE,
                 "content": message}
            )
            response = openai.ChatCompletion.create(
                model=self.__model,
                messages=update_graph_msgs
            )
            update_queries.append(response["choices"][0]["message"]["content"])

        # instead actually update the graph...
        #self.__bg.update()
        print(f"\nUpdate Queries:")
        i: int = 1
        for upt_query in update_queries:
            print(f"U.Q. {i}:\n{upt_query}")
            i += 1
