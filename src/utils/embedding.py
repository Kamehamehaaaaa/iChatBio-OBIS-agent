# from utils import utils
# from openai import OpenAI
# from sentence_transformers import SentenceTransformer
# import json

# model = SentenceTransformer("all-MiniLM-L6-v2")

# def load_dataset():
#     print("loading Areas")
#     areas = utils.getData("areaids.json", "areaid")
#     print("loading Institutes")
#     institutes = utils.getData("institutes.json", "institute")
#     print("loading datasets")
#     datasets = utils.getData("datasets.json", "dataset")
#     print("data loading complete")
#     return areas, institutes, datasets

# # keep data required for embedding only
# def format_data(dataset):
#     formatted_data = []
#     skipped_data = 0

#     for data in dataset:
#         if data.get("name", '') != '':
#             # formatted_data.append({"name":data["name"], "type":type})
#             formatted_data.append(data.get("name"))
#         elif data.get("title", '') != '':
#             # formatted_data.append({"name":data["title"], "type":type})
#             formatted_data.append(data.get("title"))
#         else:
#             # skip data
#             skipped_data += 1
    
#     print("\tdata formatted:", len(formatted_data), " data skipped:", skipped_data)
#     return formatted_data

# # def get_embedding(text):
# #     # response = client.embeddings.create(
# #     #     model="nomic-embed-text-v1.5",
# #     #     input=text
# #     # )
# #     # return response.data[0].embedding
# #     entities = [
# #         "Woods Hole Oceanographic Institution",
# #         "Florida Institute of Oceanography",
# #         "Gulf of Mexico",
# #     ]

# #     embeddings = model.encode(
# #         entities,
# #         batch_size=128,
# #         show_progress_bar=True,
# #         convert_to_numpy=True
# #     )

# def generate_embeddings(data):
#     from time import time

#     start_t = time()
#     entities = format_data(data)
    
#     embeddings = model.encode(
#         entities,
#         batch_size=128,
#         show_progress_bar=True    
#     )
#     print("embedding time:", time() - start_t)
#     return embeddings.tolist()

# def update_data_with_embeddings(data, embeddings):
#     if len(data) != len(embeddings):
#         print("data and embeddings dont match")
#         return False
    
#     for i in range(len(data)):
#         data[i]["embedding"] = embeddings[i]
    
#     return True

# def write_to_file(data, type):
#     fileName = {"area" : "areaids.json", "institute": "institutes.json", "dataset":"datasets.json"}

#     with open(fileName[type], "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=2, ensure_ascii=False)
        

# def main():
#     areas, institutes, datasets = load_dataset()
#     print("total data for embedding:", len(areas) + len(institutes) + len(datasets))
#     # print("data samples")
#     # print("areas[0]:\n", areas[0])
#     # print("institutes[0]:\n", institutes[0])
#     # print("datasets[0]:\n", datasets[0])

#     embeddings = generate_embeddings(areas)

#     update_data_with_embeddings(areas, embeddings)

#     # print(areas[0])

#     write_to_file(areas, "area")

#     embeddings_dataset = generate_embeddings(datasets)
#     update_data_with_embeddings(datasets, embeddings_dataset)
#     write_to_file(datasets, "dataset")

#     embeddings_ins = generate_embeddings(institutes)
#     update_data_with_embeddings(institutes, embeddings_ins)
#     write_to_file(institutes, "institute")

# main()

import os
os.environ["OMP_NUM_THREADS"] = "1"

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
from time import time


# --------------------------------------
# Load datasets
# --------------------------------------
def load_dataset():
    from utils import dataLoader
    print("loading Areas")
    areas = dataLoader.getData("areas")

    print("loading Institutes")
    institutes = dataLoader.getData("institutes")

    print("loading datasets")
    datasets = dataLoader.getData("datasets")

    print("data loading complete")

    return areas, institutes, datasets


# --------------------------------------
# Extract text + metadata
# --------------------------------------
def format_data(dataset):

    texts = []
    metadata = []
    skipped = 0

    for data in dataset:

        name = data.get("name") or data.get("title")

        if name:
            texts.append(name)
            metadata.append(data)
        else:
            skipped += 1

    print("\tformatted:", len(texts), " skipped:", skipped)

    return texts, metadata


# --------------------------------------
# Generate embeddings
# --------------------------------------
def generate_embeddings(texts):

    start = time()


    model = SentenceTransformer("all-MiniLM-L6-v2")

    embeddings = model.encode(
        texts,
        batch_size=256,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    embeddings = embeddings.astype("float32")

    print("embedding time:", time() - start)

    return embeddings


# --------------------------------------
# Build FAISS index
# --------------------------------------
def build_faiss_index(embeddings, metadata):

    dimension = embeddings.shape[1]

    # normalize for cosine similarity
    faiss.normalize_L2(embeddings)

    base_index = faiss.IndexFlatIP(dimension)
    index = faiss.IndexIDMap(base_index)

    # create sequential numeric ids
    ids = np.arange(len(metadata)).astype("int64")

    index.add_with_ids(embeddings, ids)

    return index

    # dimension = embeddings.shape[1]

    # # Normalize vectors for cosine similarity
    # faiss.normalize_L2(embeddings)

    # base_index = faiss.IndexFlatIP(dimension)

    # index = faiss.IndexIDMap(base_index)

    # ids = np.array([m["id"] for m in metadata]).astype("int64")

    # index.add_with_ids(embeddings, ids)

    # return index

def create_index(texts, metadata, type):

    print(f"total entities for indexing of {type}:", len(texts))

    index = generate_index(texts, metadata)

    save_index(index, metadata, type)

def generate_index(texts, metadata):
    embeddings = generate_embeddings(texts)
    index = build_faiss_index(embeddings, metadata)

    return index


# --------------------------------------
# Save index + metadata
# --------------------------------------
def save_index(index, metadata, type):

    faiss.write_index(index, f"obis_{type}.index")

    with open(f"{type}.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("FAISS index + metadata saved")

def get_matches(query, type):
    index = faiss.read_index(f"obis_{type}.index")
    q_emb = generate_embeddings([query])
    # print(q_emb.dtype)
    # print(q_emb.shape)
    distances, indices = index.search(q_emb, 10)

    # print("matches from index:", distances, indices)

    from utils import dataLoader
    metadata = dataLoader.getData(type)
    matches = []

    for i, ind in enumerate(indices[0]):
        matches.append([
            metadata[ind],
            distances[0][i]
        ])

    return matches


# --------------------------------------
# Main pipeline
# --------------------------------------
def main():

    # areas, institutes, datasets = load_dataset()

    # print("processing areas")
    # area_texts, area_meta = format_data(areas)

    # print("processing institutes")
    # inst_texts, inst_meta = format_data(institutes)

    # print("processing datasets")
    # data_texts, data_meta = format_data(datasets)

    # create_index(area_texts, area_meta, "areas")
    # create_index(inst_texts, inst_meta, "institutes")
    # create_index(data_texts, data_meta, "datasets")

    print(get_matches("Australia", "areas"))


if __name__ == "__main__":
    main()