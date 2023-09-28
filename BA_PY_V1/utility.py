def trim_quest_structure(quest_output: str):
    print(quest_output)
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
        trimmed_output = query_request[start_index:end_index + 1]
        prefixes = '''
            @PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @PREFIX owl: <http://www.w3.org/2002/07/owl#> .
            @PREFIX schema: <https://schema.org/> .
            @PREFIX ex: <http://example.org/> .
            '''
        trimmed_output = f"{prefixes}\n\n{trimmed_output}"
    else:
        trimmed_output = query_request[start_index:end_index + 1]

    return trimmed_output
