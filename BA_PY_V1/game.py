import json

import openai_facade
import quest
import consequence
import blazegraph
import color_console
from pymantic import sparql
from utility import create_message as Message
from utility import trim_quest_structure
from utility import reorder_query_triplets
from utility import correct_query


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
        self.__coco = color_console.ColorConsole()

        # node graph node types here; currently just selected examples
        self.__node_types = '''
        WorldLocation, 
        Dragon, Human, Wolf, 
        Item, Weapon, Sword, WarHammer, Apparel, 
        WorldObject,
        WorldResource,
        Treasure
        '''

    def run(self):
        self.prompt()
        first_response = self.get_response()
        self.__coco.coco_print(f'''{first_response["choices"][0]["message"]["content"]}''')

        self.__coco.coco_game('''Welcome to the town of Eich wandering loner! You may now call this your new home. Help the villagers, explore the world and seek new challenges in form of quests.''')

        while True:
            user_answer = self.__coco.coco_input("What do you want to do? Explore, request a quest, go on a quest or do you want to quit?")
            chosen_path = self.choose_path(user_answer)
            self.__coco.coco_debug(f"Chosen Path - {chosen_path}")

            if chosen_path == "explore":
                self.handle_exploration()
            elif chosen_path == "quest_generation":
                self.handle_quest_request()
            elif chosen_path == "quest_progressing":
                self.handle_quest_progression()
            elif chosen_path == "quit":
                self.__coco.coco_print("Resetting the graph...")
                self.__bg.reset_graph()
                self.__coco.coco_print("Quitting game...")
                break
            elif chosen_path == "undefined":
                self.__coco.coco_print("Your request can't be realized! Let's try again...")
                continue
            else:
                self.__coco.coco_print("An error occurred! Let's try again...")
                continue

    def choose_path(self, user_request: str):
        decision_msgs = []
        dummy_functions = [{
            "name": "path_selection",
            "description": "Decides based on the provided enum which path the game loop should step in.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selected_path": {
                        "type": "string",
                        "enum": ["explore", "quest_generation", "quest_progressing", "quit", "undefined"],
                        "description": '''The path that should be chosen. 
                        "explore" if the player wants to continue exploring, 
                        "quest_generation" if he requests a new quest,
                        "quest_progression" if he wants to go on a quest,
                        "quit" if he wants to quit the game, 
                        and "undefined" if you can't assign one of the other options.''',
                    }
                }, "required": ["selected_path"],
            }
        }]

        message = f'''The player was asked what he wants to do and this was his answer: "{user_request}". 
                Now decide based on his answer if the player wants to continue exploring, if he requests a new quest, if 
                he wants to play an already generated quest, or if he wants to quit the game completely.'''

        decision_msgs.append(Message(message, self.SYSTEM_ROLE))
        response = self.__gpt_facade.make_function_call(decision_msgs, dummy_functions, "path_selection", 0.1)

        response_arguments = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
        path = response_arguments.get("selected_path")

        return path

    def handle_quest_request(self):
        while True:
            user_request = self.__coco.coco_input("Please tell us what quest you want to play.")
            self.__coco.coco_print("Starting quest generation...")
            extracted_nodes = self.get_graph_knowledge(user_request)
            gen_quest = self.generate_quest(user_request, extracted_nodes)

            if not self.was_quest_generated(gen_quest):
                continue

            gen_quest = self.correct_structure(gen_quest)

            if self.is_quest_valid(gen_quest):
                quest_answer = self.__coco.coco_input("Do you want to accept the quest?")
                if self.is_accepting_quest(quest_answer):
                    self.__coco.coco_print("The quest suggestion was accepted. Completing generation...")
                    gen = self.convert_quest(gen_quest)
                    self.__quests.append(gen)
                    consequences = []
                    for st in gen.sub_tasks:
                        for cons in st["Task_Consequences"]:
                            consequences.append(cons["Description"])
                    self.update_graph_based_on_consequences(consequences, extracted_nodes)

                    self.__coco.coco_game(f"Here is your new quest:\nName: {gen.name}\nDesc: {gen.short_desc}\nSrc:  {gen.source}")
                    self.clear_triplets()
                    break
                else:
                    remain_answer = self.__coco.coco_input("Do you want to request another quest?")
                    if self.continue_requesting(remain_answer):
                        continue
                    else:
                        break
            else:
                self.__coco.coco_print("Generated quest was not valid!")
                self.clear_triplets()
                continue

    def handle_quest_progression(self):
        if len(self.__quests) == 0:
            alternative_selection = self.__coco.coco_input("Sorry, there are currently no quests available. Do you want to request a quest or to explore the world?")

            # change state based on alt selection or return to loop beginning
        else:
            quest_selection = "What quest do you want to play? Here are your options:"
            quest_number = 1
            for quest_option in self.__quests:
                quest_selection = f"{quest_selection}\n{quest_number}. Name: {quest_option.name}.\n Desc: {quest_option.description}."
                quest_number += 1
            selected_quest = self.__coco.coco_input(quest_selection)

            # select and start quest
            current_quest = self.__quests.__getitem__(0)

            current_task_index = 0
            while True:
                # start task 1
                current_task = current_quest.sub_tasks.__getitem__(current_task_index)

                while True:

                    # if done...
                    break

                # progress... loop...
                current_task_index += 1

                # finish
                break

    def handle_exploration(self):
        self.__coco.coco_game("You start exploring...")
        while True:
            next_action = self.__coco.coco_input("What do you want to do next?")
            if self.continue_exploring(next_action):
                validation_output = self.validate_exploration(next_action)
                valid = validation_output.get("is_request_valid")
                reaction = validation_output.get("action_reaction")
                explanation = validation_output.get("validity_explanation")
                if valid:
                    self.update_graph_based_on_explor_actions(next_action, reaction, self.__last_queried_triplets)
                    self.clear_triplets()
                    self.__coco.coco_game(reaction)
                    # updating generated quests ? How ?!
                else:
                    self.__coco.coco_print(f"Your requested action can't be performed, see: {explanation}")
                    self.__coco.coco_game(reaction)
                continue
            else:
                self.__coco.coco_game("Finish exploring...")
                break

    def validate_exploration(self, exploration_request: str):
        extracted_nodes = self.get_graph_knowledge(exploration_request)
        self.__last_queried_triplets = extracted_nodes.copy()

        validity_function = [{
            "name": "validity_check",
            "description": "Decides based on the given user request, the narrative and queried graph node triplets if the request is possible and therefore valid.",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_request_valid": {
                        "type": "boolean",
                        "description": "True if the action contained by the exploration request can be done by the player, both in terms of its capabilities and in terms of what the game world, the narrative, and general logic allow and has to offer.",
                    },
                    "action_reaction": {
                        "type": "string",
                        "description": "The game's reaction on the user's action. This should be a sentence describing the user's action, if valid, or that should be stating that the action can not be performed due to some reasons, if not valid.",
                    },
                    "validity_explanation": {
                        "type": "string",
                        "description": "The explanation and description of why the action request is valid or invalid.",
                    }
                }, "required": ["is_quest_valid", "action_reaction", "validity_explanation"],
            }
        }]

        validation_msgs = []

        message = f'''Now only validate if the user's request for performing an arbitrary action can be performed by the 
        player, both in terms of its capabilities and in terms of what the game world, the narrative, and general 
        logic allow and have to offer. Furthermore, small actions that don't change the state of the world, like cutting 
        a single tree, going on a walk, picking some flowers, or building a snow man in a snowy region, can normally be 
        performed without any issues.
        Here is the user's exploration request: "{exploration_request}".
        Here is the narrative used as a base for the game world: "{narrative.get_narrative()}"
        Here are some graph node triplets that were queried based on the request: "{extracted_nodes}"'''

        validation_msgs.append(Message(message, self.SYSTEM_ROLE))
        response = self.__gpt_facade.make_function_call(validation_msgs, validity_function, "validity_check", 0.25)

        response_arguments = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])

        return response_arguments

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

    def continue_exploring(self, user_request: str):
        decision_msgs = []
        dummy_functions = [{
            "name": "keep_exploring_check",
            "description": "Decides based on the provided player decision of what to do next, if he wants to continue exploring or if he wants to stop and do something else.",
            "parameters": {
                "type": "object",
                "properties": {
                    "continue_exploring": {
                        "type": "boolean",
                        "description": "True if the wants to continue exploring, false if he wants to start or request a quest or if he wants to quit the game.",
                    }
                }, "required": ["continue_exploring"],
            }
        }]

        message = f'''The player was asked what he wants to do next and this was his answer: "{user_request}". 
        Now decide based on his answer if the player wants to continue exploring, or if he wants to quit exploring. 
        Generally, you can check if the player explicitly wants to quit exploring or if he specifically asks for 
        starting or generating a quest. If his answer suggests that he wants to perform some actions, it can be assumed
        he wants to continue exploring.'''

        decision_msgs.append(Message(message, self.SYSTEM_ROLE))
        response = self.__gpt_facade.make_function_call(decision_msgs, dummy_functions, "keep_exploring_check", 0.25)

        response_arguments = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
        keep_exploring = response_arguments.get("continue_exploring")

        return keep_exploring

    def continue_requesting(self, answer: str):
        decision_msgs = []
        dummy_functions = [{
            "name": "continue_requesting_check",
            "description": "Decides based on the provided player answer, if he wants to request another quest, or if he wants to do something else.",
            "parameters": {
                "type": "object",
                "properties": {
                    "continue_requesting": {
                        "type": "boolean",
                        "description": "True if the player wants to request another quest, false if he does not.",
                    }
                }, "required": ["continue_exploring"],
            }
        }]

        message = f'''The player was asked if he wants to continue requesting quests, this was his answer: "{answer}". 
                Now decide based on his answer if the player wants to continue requesting, or if he wants to stop.
                You can generally check if the player explicitly wants to continue requesting, perhaps with a simple 
                'yes,' or if they express a different desire than requesting a quest.'''

        decision_msgs.append(Message(message, self.SYSTEM_ROLE))
        response = self.__gpt_facade.make_function_call(decision_msgs, dummy_functions, "continue_requesting_check", 0.1)

        response_arguments = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
        keep_requesting = response_arguments.get("continue_requesting")

        return keep_requesting

    def reset_graph(self):
        self.__bg.clear_graph()
        self.__bg.load_graph()

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
            f"Decide which of the given node types need to be queried based of the following user request: {request}",
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
            self.__coco.coco_debug(f"Args: {function_args}")
            # this is the output of the actual function
            queried_nodes = function_to_call(
                required_nodes=function_args.get("required_nodes"),
                required_objective=function_args.get("required_objective"),
            )
            return queried_nodes

    def query_nodes(self, required_nodes: [], required_objective: str):
        obj_triplets = []
        deeper_obj_triplets = []
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

            deeper_search_queries = self.generate_query_from_attributes(obj_triplets)

            for query in deeper_search_queries:
                triplets = reorder_query_triplets(self.__bg.query(query))
                for triplet in triplets:
                    deeper_obj_triplets.append(triplet)

        # multiple tries, because the query generation tends to be not 100% valid
        try_counter = 0
        while try_counter < 3:
            response_query = self.generate_query_from_types(required_nodes)
            try_counter += 1
            try:
                query_result = self.__bg.query(response_query)
            except Exception as e:
                self.__coco.coco_debug(f"Invalid query! #Tries: {try_counter}!\nError: {e}")
                if try_counter == 3:
                    self.__coco.coco_print(f"No valid query was generated in {try_counter} tries!")
            else:
                node_triplets = reorder_query_triplets(query_result)
                break

        node_set = set(node_triplets)
        obj_set = set(obj_triplets)
        deeper_set = set(deeper_obj_triplets)
        combined_set = obj_set.union(node_set)
        combined_set = combined_set.union(deeper_set)
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

        self.__coco.coco_debug(f"Type-ish node query:\n{response_query}")

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

        return response_query

    def generate_query_from_attributes(self, specific_node_triplets):
        msgs = []
        query_nodes_function = [{
            "name": "dummy_query_nodes",
            "description": "Queries the nodes from a knowledge graph based on given node names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "required_nodes": {
                        "type": "string",
                        "description": "An array of strings naming the nodes that should be queried from a knowledge graph.",
                    }
                }, "required": ["required_nodes"],
            }
        }]
        msgs.append(Message(
            f"Here is a list of rdf triplets describing an already queried node and its attributes: {specific_node_triplets}",
            self.SYSTEM_ROLE))
        msgs.append(Message(
            f"Now select the triplets' objects that should be leading to another node instance providing more information from the graph. Avoid selecting types and labels. Select only values that lead to other nodes.",
            self.SYSTEM_ROLE))
        response = self.__gpt_facade.make_function_call(msgs, query_nodes_function, "dummy_query_nodes")

        response_message = response["choices"][0]["message"]

        function_args = json.loads(response_message["function_call"]["arguments"])
        self.__coco.coco_debug(f"Args (deeper nodes): {function_args}")

        try:
            required_nodes_list = function_args.get("required_nodes").split(', ')
        except AttributeError as ae:
            self.__coco.coco_debug(f"List error at \"required_nodes\": {ae}")
            required_nodes_list = function_args.get("required_nodes")
        queries = []
        for node in required_nodes_list:
            query = '''PREFIX ex: <http://example.org/>

SELECT ?subject ?property ?value
WHERE {
  ?subject ?property ?value .
  FILTER (?subject = ex:''' + node + ''')
}
'''
            queries.append(query)

        return queries

    def generate_quest(self, quest_request: str, extracted_nodes):
        msgs = self.__messages.copy()
        msgs.append(Message(f"Take a deep breath and think about what should be part of a good rpg quest, then build the quest's story around a few of those given graph nodes extracted from the knowledge graph: {extracted_nodes}", self.USER_ROLE))
        msgs.append(Message(f"Generate a quest for the following player request, using only the given structure:\n{quest_request}", "system"))
        request_response = self.__gpt_facade.get_response(msgs, 1.0)  # self.get_response(1.0)
        generated_quest = trim_quest_structure(request_response["choices"][0]["message"]["content"])
        self.__coco.coco_debug(generated_quest)
        #self.__quests.append(generated_quest)
        return generated_quest

    def correct_error(self, invalid_quest_structure: str, error_msg):
        # do call with command of "repairing" structure
        try_count = 1

        while True:
            self.__coco.coco_debug(f"Correction {try_count}")
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
                self.__coco.coco_debug(f"Another Error was still found after {try_count} corrections: {e}")
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
                self.__coco.coco_debug(f"A JSON decode Error occurred. Correction-try: {counter}")
                generated_quest_structure = self.correct_error(generated_quest_structure, jde)
                continue
            except Exception as e:
                counter += 1
                self.__coco.coco_debug(f"The structure wasn't correctly formatted. Correction-try: {counter}")
                generated_quest_structure = self.correct_error(generated_quest_structure, e)
                continue

            try:
                q_sub_tasks = json_quest["SubTasks"]
                for task in q_sub_tasks:
                    task_consequences = task["Task_Consequences"]
            except KeyError as ke:
                counter += 1
                self.__coco.coco_debug(f"An KeyError occurred when accessing the json-loaded quest structure:\n{ke}\nRe-try: {counter}")
                generated_quest_structure = self.correct_error(generated_quest_structure, ke)
                continue
            except Exception as e:
                counter += 1
                self.__coco.coco_debug(f"Another error occurred when accessing the json-loaded quest structure:\n{e}\nRe-try: {counter}")
                generated_quest_structure = self.correct_error(generated_quest_structure, e)
                continue
            else:
                break

        return generated_quest_structure

    def was_quest_generated(self, generated_quest_structure: str):
        if generated_quest_structure.find("{") == -1 or generated_quest_structure.find("}") == -1:
            self.__coco.coco_print(f"Quest wasn't generated:\n{generated_quest_structure}")
            return False
        else:
            return True

    def is_quest_valid(self, generated_quest_structure: str):
        # checking if there is any structure
        if not self.was_quest_generated(generated_quest_structure):
            return False

        while True:
            try:
                json_quest = json.loads(f'{generated_quest_structure}')
            except json.JSONDecodeError as jde:
                self.__coco.coco_debug(f"A JSON decode Error occurred: {jde}")
                return False
            except Exception as e:
                self.__coco.coco_debug(f"The structure wasn't correctly formatted: {e}")
                return False
            else:
                break

        while True:
            try:
                q_sub_tasks = json_quest["SubTasks"]
                for task in q_sub_tasks:
                    task_consequences = task["Task_Consequences"]
                    for des in task_consequences:
                        self.__coco.coco_debug(f"\nC.D: {des}")
            except KeyError as ke:
                self.__coco.coco_debug(f"An KeyError occurred when accessing the json-loaded quest structure:\n{ke}\n")
                return False
            except Exception as e:
                self.__coco.coco_debug(f"Another error occurred when accessing the json-loaded quest structure:\n{e}\n")
                return False
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
        consistent with the narrative and the queried graph node triplets. If some knowledge is provided only by the 
        graph node triplets, assume it was just not mentioned in the narrative, and that it's therefore still valid. 
        Also make sure that it is logical and playable. Here is the generated quest again:\n{generated_quest_structure}
        And here are the queried graph node triplets again:\n{self.__last_queried_triplets}'''

        validation_msgs.append(Message(message, self.SYSTEM_ROLE))
        response = self.__gpt_facade.make_function_call(validation_msgs, validity_function, "validity_check", 0.25)

        response_arguments = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
        valid = response_arguments.get("is_quest_valid")
        explanation = response_arguments.get("validity_explanation")
        self.__coco.coco_debug(f"Quest Validation:\n{valid}\n{explanation}")

        return valid

    def is_accepting_quest(self, answer: str):
        decision_msgs = []
        dummy_functions = [{
            "name": "accept_quest_check",
            "description": "Decides based on the provided player answer, if he wants to accept the provided quest or if he wants to stop deny it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "accept_quest": {
                        "type": "boolean",
                        "description": "True if the wants to accept the quest, false if he denies it or if he expresses dislikes.",
                    }
                }, "required": ["continue_exploring"],
            }
        }]

        message = f'''The player was asked if he wants to accept the suggested quest, this was his answer: "{answer}". 
                Now decide based on his answer if the player wants to accept the quest, or if he wants to deny it, 
                resulting in a new iteration of request and generation. 
                Generally, you can check if the player explicitly wants to accept it, maybe with a simple yes, or if he 
                expresses some type of dislikes, like a simple no or by talking bad about the suggested quest.'''

        decision_msgs.append(Message(message, self.SYSTEM_ROLE))
        response = self.__gpt_facade.make_function_call(decision_msgs, dummy_functions, "accept_quest_check", 0.1)

        response_arguments = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
        accept_quest = response_arguments.get("accept_quest")

        return accept_quest

    def clear_triplets(self):
        self.__last_queried_triplets.clear()

    def convert_quest(self, generated_structure: str):
        json_quest = json.loads(f'{generated_structure}')
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

    def update_graph_based_on_consequences(self, consequences, node_triplets):
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
            ones. Take a step back and think about every predicates true meaning, so you can apply them truthfully and 
            don't accidentally create a redundant predicate. Below is a comprehensive list of the available predicates:
            {predicates}
            Here is the task consequence:
            "{cons}".\n
            When generating the query, only return the code of the query, nothing else, so no additional descriptions, 
            and please use the following pattern for the query:
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
            update_queries.append(correct_query(response["choices"][0]["message"]["content"]))
            usage = response["usage"]
            self.__coco.coco_debug(f"Token Info: \n{usage}")

        self.__coco.coco_debug(f"Update Queries:")
        i: int = 1
        for upt_query in update_queries:
            self.__coco.coco_debug(f"U.Q. {i}:\n{upt_query}")
            try:
                self.__bg.update(upt_query)
            except sparql.SPARQLQueryException:
                upt_query = correct_query(upt_query)
                self.__bg.update(upt_query)
            i += 1

    def update_graph_based_on_explor_actions(self, action_request, system_reaction, node_triplets):
        update_graph_msgs = self.__messages.copy()
        sparql_pattern = "DELETE {} INSERT {} WHERE {}"
        optional_block = "OPTIONAL {}"

        predicates = self.__bg.query('''
            PREFIX ex: <http://example.org/>

            SELECT DISTINCT ?predicate
            WHERE {
                ?subject ?predicate ?object
            }''')
        predicates = reorder_query_triplets(predicates)

        message = f'''Here is a list of RDF triplets that were taken from a knowledge graph:
        "{node_triplets}".\n
        In our medieval RPG game, players can freely explore the game world beyond structured quests. During these 
        explorations, they can take actions that potentially alter the state of the game world and its underlying 
        knowledge graph. Your challenge is to craft a single SparQL query, using the provided triplets, to logically 
        update relevant triplets impacted by the player's actions. Distinguish between changes essential to the graph 
        and those that are minor or inconsequential. When a player creates something new, like a cabin, or when an 
        object or resource, which should naturally exist in the game world based on the setting, is mentioned, you may 
        add a new node to the graph, including all necessary attributes.
        Emphasize minimal node deletion, with a focus on altering or removing specific attributes when necessary. This 
        query is exclusively for graph updates and does not involve condition checking or complete node deletions. 
        Prioritize the use of existing predicates over introducing new ones. Ensure a thoughtful approach to the meaning 
        of each predicate and type, applying them accurately to avoid redundancy or the creation of unnecessary 
        predicates or types. Use types exclusively for assigning identical types to nodes, without combining those types 
        with other predicates. Below is a comprehensive list of the available predicates:
        {predicates}
        And here is a comprehensive list of the available types that new nodes can have: 
        "{self.__node_types}".
        Here is the user's action request:
        "{action_request}".
        Here is the game's description of and reaction to the player's action: 
        "{system_reaction}".
        This description may help defining what actually happens in the world, not only what the player requested to do.
        When generating the query, only return the code of the query, nothing else, so no additional descriptions, 
        and please use the following pattern for the query:
        "{sparql_pattern}".
        Use {optional_block} inside the WHERE block if a WHERE check is really necessary, but it could be the first time 
        the triple is set. Always write out triplets completely, even if they share the same subject, and remember to 
        place the finishing '.' at the end of each triplet. And if there is nothing to update, please return an query 
        with empty brackets, following the provided pattern. Also, when generating the query, always use this prefixes:
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX ex: <http://example.org/>
        '''
        update_graph_msgs.append(Message(message, self.SYSTEM_ROLE))
        response = self.__gpt_facade.get_response(update_graph_msgs, 0.2)
        update_query = correct_query(response["choices"][0]["message"]["content"])

        self.__coco.coco_debug(f"Update Query:\n{update_query}")
        try:
            self.__bg.update(update_query)
        except sparql.SPARQLQueryException:
            upt_query = correct_query(update_query)
            self.__bg.update(upt_query)
