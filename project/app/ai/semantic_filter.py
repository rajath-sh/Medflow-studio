import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

FILTERS = {
    "older than": "age >",
    "younger than": "age <",
    "female": "gender = female",
    "male": "gender = male",
}

def parse_semantic_query(query: str):
    query = query.lower()
    filters = {}

    if "older than" in query:
        age = int(query.split("older than")[1].split()[0])
        filters["min_age"] = age

    if "younger than" in query:
        age = int(query.split("younger than")[1].split()[0])
        filters["max_age"] = age

    if "female" in query:
        filters["gender"] = "female"

    if "male" in query:
        filters["gender"] = "male"

    return filters
