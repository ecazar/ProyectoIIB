from sentence_transformers import SentenceTransformer, CrossEncoder, util
import torch
import torch.nn.functional as F
from backend.preprocess_data import get_vit_embedding, clip_model

from backend.preprocess_data import load_data

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def search_query(query, top_k=5):
    df, clip_embeddings, vit_embeddings = load_data()

    # Retrieval uso de CLIP para filtrar rapidamente
    initial_k = 30
    query_emb = clip_model.encode(query, convert_to_tensor=True)
    cos_scores = util.cos_sim(query_emb, clip_embeddings)[0]
    top_results = torch.topk(cos_scores, k=initial_k)

    candidates = []
    for score, idx in zip(top_results.values, top_results.indices):
        item = df.iloc[int(idx)].to_dict()
        item['clip_score'] = float(score)
        candidates.append(item)

    # Reranking
    final_results = []
    # ---Si es Text la query (Cross Encoder)
    if isinstance(query, str):
        sentence_combinations = []
        for item in candidates:
            # Concatenamos atributos para crear una descripción para el modelo
            product_desc = f"{item['ProductTitle']}. Category: {item['SubCategory']}. Color: {item['Colour']}. Usage: {item['Usage']}"
            sentence_combinations.append([query, product_desc])
        # Prediccion del Cross-Encoder
        similarity_scores = cross_encoder.predict(sentence_combinations)
        # Nuevos scores
        for i, item in enumerate(candidates):
            item['rerank_score'] = float(similarity_scores[i])
        # ordenamos del mejor al peor
        results = sorted(candidates, key=lambda x: x['rerank_score'], reverse=True)[:top_k]
        return results
    # ---Si es Img la query (VIT)
    else:
        query_vit_emb = get_vit_embedding(query)

        final_scores = []
        for idx in top_results.indices:
            cand_vit_emb = vit_embeddings[idx]
            # Similitud de coseno entre los vectores ya guardados
            score = F.cosine_similarity(query_vit_emb, cand_vit_emb.unsqueeze(0)).item()
            item = df.iloc[idx].to_dict()
            item['rerank_score'] = score
            final_scores.append(item)
        # ordenamos del mejor al peor
        results = sorted(final_scores, key=lambda x: x['rerank_score'], reverse=True)[:top_k]
        return results

