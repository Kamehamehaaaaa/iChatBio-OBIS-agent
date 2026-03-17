# from collections import defaultdict

# def build_ngram_index(metadata, n=3):

#     index = defaultdict(set)

#     for i, entity in enumerate(metadata):

#         text = entity["name"]

#         grams = generate_ngrams(text, n)

#         for g in grams:
#             index[g].add(i)

#     return index

# def search_ngram(query, index, metadata, n=3):

#     query_grams = generate_ngrams(query, n)

#     scores = {}

#     for g in query_grams:

#         if g not in index:
#             continue

#         for entity_id in index[g]:

#             scores[entity_id] = scores.get(entity_id, 0) + 1

#     return scores

from utils import dataLoader

def generate_ngrams(text, n=3):
    text = text.lower()
    text = text.replace(" ", "_")
    return [text[i:i+n] for i in range(len(text)-n+1)]


def jaccard_score(query_ngrams, entity_name, n=3):
    entity_ngrams = set(generate_ngrams(entity_name, n))
    return len(query_ngrams & entity_ngrams) / len(query_ngrams | entity_ngrams)

def format_data(dataset):
    texts = []
    metadata = []
    skipped = 0

    for data in dataset:

        name = data.get("name") or data.get("title")

        if name:
            metadata.append(data)
        else:
            skipped += 1

    print("\tformatted: skipped:", skipped)

    return metadata

def search(query, type, top=10):
    metadata = dataLoader.getData(type)
    metadata = format_data(metadata)
    results = []
    print("in ngrams",query)
    query_ngrams = set(generate_ngrams(query))
    for i, entity in enumerate(metadata):
        name = entity.get('name') if entity.get('name', '') != '' else entity.get('title')
        score = jaccard_score(query_ngrams, name)
        if score > 0:
            results.append((entity, score))

    results.sort(key=lambda x: x[1], reverse=True)

    return results[:top]

# search("Australia", "areas")