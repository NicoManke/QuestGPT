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
        self.add_message(f"Here is a structure describing a quest for a video rpg game: \n{quest_structure.get_quest_structure()}", self.SYSTEM_ROLE)
        # add narrative
        self.add_message(f"Here is the narrative of the world our game takes place in: \n{narrative.get_narrative()}", self.SYSTEM_ROLE)
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
            )
            return queried_nodes

    def query_nodes(self, required_nodes: []):
        bg = blazegraph.BlazeGraph(self.__server_address)
        try_counter = 0

        # multiple tries, because the query generation tends to be not 100% valid
        while try_counter < 3:
            response_query = self.generate_query(required_nodes)
            try_counter += 1
            try:
                query_result = bg.query(response_query)
            except Exception as e:
                print(f"\nInvalid query! #Tries: {try_counter}")
                if try_counter == 3:
                    print(f"No valid was generated in {try_counter} tries!")
            else:
                print(f"\nQuery output vars:\n{query_result['head']['vars']}")
                # remaining code here...?
                break

        # getting all values and only the values from the output
        values = []
        for var in query_result['head']['vars']:
            for binding in query_result['results']['bindings']:
                value = binding[var]['value']
                values.append(value)
                # print(f"{var}: {value}")
        var_count = len(query_result['head']['vars'])
        val_count = len(query_result['results']['bindings'])
        # basically recombining the triplets
        triplets = []
        print("\nTriplets:")
        for i in range(val_count):
            triplet = ""
            for j in range(var_count):
                triplet = f"{triplet}{values[i + j * val_count]} "
            triplets.append(triplet)
            print(triplet)
        return triplets

    def generate_query(self, required_nodes):
        msgs = []
        node_query_request = f"Give me a SparQL query to retrieve all nodes, including their properties' values, of the following types and their subclasses: ({required_nodes})"
        prefixes = '''
                    Also use for this the following prefixes and include them in the query:
                    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
                    @prefix owl: <http://www.w3.org/2002/07/owl#> .
                    @prefix schema: <https://schema.org/> .
                    @prefix ex: <http://example.org/> .
                '''
        only_code_command = "Only return the code for the query, nothing else."
        msgs.append(
            {"role": self.SYSTEM_ROLE,
             "content": f"{node_query_request}. {prefixes}. {only_code_command}"}
        )
        response = openai.ChatCompletion.create(
            model=self.__model,
            messages=msgs
        )
        response_query = utility.correct_query(response["choices"][0]["message"]["content"])

        print(f"\nNode query:\n{response_query}")

        return response_query

    def generate_quest(self, quest_request: str, extracted_nodes):
        self.add_message(f"Build the quest's story around some of these given graph nodes extracted from the narrative: {extracted_nodes}")
        self.add_message(f"Generate a quest for the following player request, using only the given structure:\n{quest_request}", "system")
        request_response = self.get_response(1.0)
        generated_quest = utility.trim_quest_structure(request_response["choices"][0]["message"]["content"])
        self.__quests.append(generated_quest)
        return generated_quest

    def correct_structure(self, invalid_quest_structure: str):
        # do call with command of "repairing" structure
        try_count = 0

        while True:
            print(f"Correction {try_count}")
            try_count += 1
            # do correction call with {invalid_quest_structure}
            corrected_structure = invalid_quest_structure
            try:
                loaded_corrected_structure = json.loads(corrected_structure)
            except Exception as e:
                print(f"Error: {e}")
                if try_count > 2:
                    break
            else:
                return loaded_corrected_structure
            break


    def is_quest_valid(self, quest_structure: str):
        # checking if there is any structure
        if quest_structure.find("{") == -1 or quest_structure.find("}") == -1:
            print(quest_structure)
            return False
        # catching the case of a not correctly formatted structure
        try:
            json_quest = json.loads(f'{quest_structure}')
        except Exception as e:
            print("The structure wasn't correctly formatted. (Maybe try correcting the structure...")
            print(f"See the error message:\n{e}")
            return False

        q_sub_tasks = json_quest["SubTasks"]
        for task in q_sub_tasks:
            task_consequence = task["Task_Consequences"]
            self.generate_consequence(task_consequence)

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
        \n{quest_structure}'''

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
            valid = bg.validate_quest(quest_structure) and valid

        return valid

    def generate_consequence(self, task_consequence_description: str):
        # function call for interpreting the abstract task consequence description
        cons_types = ["spawn_new_object",
                      "move_object",
                      "remove_object",
                      "change_parameter",
                      "change_state",
                      "play_sequence"]
        msgs = []
        convert_consequence_function = [{
            "name": "convert_consequence",
            "description": "Converts...",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "A description of the consequence and its influences on the game world.",
                    },
                    "cons_type": {
                        "type": "string",
                        "description": "The which the consequence can be assigned to.",
                    },
                    "cons_object": {
                        "type": "string",
                        "description": "The reference to the object on which the consequence is performed.",
                    },
                    "param": {
                        "type": "string",
                        "description": "The parameter of the object that will be changed as part of the consequence.",
                    },
                    "value": {
                        "type": "string",
                        "description": "The new value for the param property.",
                    }
                },
                "required": ["description", "cons_type", "cons_object", "param", "value"],
            }
        }]
        msgs.append(
            {"role": self.SYSTEM_ROLE,
             "content":
                 f"Decide which of the given types fits the upcoming description for a consequence the most. The types: {cons_types}"}
        )
        msgs.append(
            {"role": self.SYSTEM_ROLE,
             "content":
                 f"Here is the description of the consequence: {task_consequence_description}"}
        )
        msgs.append(
            {"role": self.SYSTEM_ROLE,
             "content":
                 f"For the description parameter just use the given description."}
        )
        msgs.append(
            {"role": self.SYSTEM_ROLE,
             "content":
                 "And decide what objects needs its parameter changed to a new value."}
        )
        response = openai.ChatCompletion.create(
            model=self.__model,
            messages=msgs,
            functions=convert_consequence_function,
            function_call={"name": "convert_consequence"},
        )
        response_message = response["choices"][0]["message"]
        if response_message.get("function_call"):
            available_functions = {
                "convert_consequence": self.convert_consequence,
            }
            function_name = response_message["function_call"]["name"]
            function_to_call = available_functions[function_name]
            function_args = json.loads(response_message["function_call"]["arguments"])
            new_consequence = function_to_call(
                description=task_consequence_description,
                cons_type=function_args.get("cons_type"),
                cons_object=function_args.get("cons_object"),
                param=function_args.get("param"),
                value=function_args.get("value"),
            )
            new_consequence.trigger()  # debug!
            self.__consequences.append(new_consequence)
        else:
            self.__consequences.append(self.convert_consequence(f"Failed to generate: {task_consequence_description}"))

    def convert_consequence(self, description, cons_type, cons_object, param, value):
        new_consequence = consequence.Consequence(description, cons_type, cons_object, param, value)
        return new_consequence

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