def create_message(content: str, role: str):
    return {"role": role, "content": content}


def trim_quest_structure(quest_output: str):
    start_index = quest_output.find("{")

    end_index = quest_output.rfind("}")

    trimmed_output = quest_output[start_index:end_index + 1]

    trimmed_output = trimmed_output.replace("json", "")

    return trimmed_output


def correct_query(query_request: str):
    start_index = query_request.upper().find("PREFIX")

    end_index = query_request.rfind("}")

    if start_index == -1:
        start_index = query_request.upper().find("SELECT")
        if start_index == -1:  # is update query (which don't have a 'SELECT')
            start_index = query_request.upper().find("DELETE")
        trimmed_output = query_request[start_index:end_index + 1]
        prefixes = '''
# fixed by code 
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX schema: <https://schema.org/>
PREFIX ex: <http://example.org/>
'''
        trimmed_output = f"{prefixes}\n\n{trimmed_output}"
    else:
        trimmed_output = query_request[start_index:end_index + 1]

    return trimmed_output


def reorder_query_triplets(query_result):
    # getting all values and only the values from the output
    values = []
    for var in query_result['head']['vars']:
        for binding in query_result['results']['bindings']:
            value = trim_triplets(binding[var]['value'])
            values.append(value)
    var_count = len(query_result['head']['vars'])
    val_count = len(query_result['results']['bindings'])

    # basically recombining the triplets
    triplets = []
    #print("\nTriplets:")
    for i in range(val_count):
        triplet = ""
        for j in range(var_count):
            triplet = f"{triplet}{values[i + j * val_count]} "
        triplets.append(triplet)
        #print(triplet)
    return triplets


def trim_triplets(triplet_part: str):
    triplet_part = triplet_part.replace("http://example.org/", "")
    triplet_part = triplet_part.replace("http://www.w3.org/1999/02/22-rdf-syntax-ns#", "")
    triplet_part = triplet_part.replace("http://www.w3.org/2000/01/rdf-schema#", "")
    triplet_part = triplet_part.replace("http://www.w3.org/2002/07/owl#", "")
    return triplet_part


def remove_line_breaks(text: str):
    return text.replace('\n', ' ')
