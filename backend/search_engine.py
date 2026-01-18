from sentence_transformers import SentenceTransformer, CrossEncoder, util
import torch
import torch.nn.functional as F
from backend.preprocess_data import get_vit_embedding, clip_model
from backend.preprocess_data import load_data

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')


def search_query(text=None, image=None, top_k=5):
    # Validación básica
    if not text and not image:
        raise ValueError("Debes pasar texto, imagen o ambos")

    df, clip_embeddings, vit_embeddings = load_data()

    # RETRIEVAL con CLIP
    #####################
    initial_k = 30
    scores = []

    # Si hay texto, calculamos score
    if text:
        text_emb = clip_model.encode(text, convert_to_tensor=True)
        text_scores = util.cos_sim(text_emb, clip_embeddings)[0]
        scores.append(text_scores)

    # Si hay imagen, calculamos score
    if image:
        # clip_model.encode maneja PIL Images automáticamente
        image_emb = clip_model.encode(image, convert_to_tensor=True)
        image_scores = util.cos_sim(image_emb, clip_embeddings)[0]
        scores.append(image_scores)

    # Combinar scores
    if len(scores) > 1:
        # Promedio para búsqueda híbrida
        combined_scores = torch.stack(scores).mean(dim=0)
    else:
        # Solo uno de los dos
        combined_scores = scores[0]

    top_results = torch.topk(combined_scores, k=initial_k)

    candidates = []
    for score, idx in zip(top_results.values, top_results.indices):
        item = df.iloc[int(idx)].to_dict()
        item["clip_score"] = float(score)
        candidates.append(item)


    # RERANKING
    #############
    # Caso A: HÍBRIDO (Texto + Imagen)
    if text and image:
        query_vit_emb = get_vit_embedding(image)
        sentence_combinations = []
        for item in candidates:
            desc = f"{item['ProductTitle']}. Color: {item['Colour']}"
            sentence_combinations.append([text, desc])

        cross_scores = cross_encoder.predict(sentence_combinations)

        for i, item in enumerate(candidates):
            idx = df.index[df['ProductId'] == item['ProductId']][0]
            vit_score = F.cosine_similarity(query_vit_emb, vit_embeddings[idx].unsqueeze(0)).item()
            # Híbrido: Peso al texto (cross) y a la similitud visual (vit)
            item["rerank_score"] = float(0.5 * cross_scores[i] + 0.5 * vit_score)

    # Caso B: SOLO TEXTO
    elif text:
        sentence_combinations = []
        for item in candidates:
            desc = f"{item['ProductTitle']}. Color: {item['Colour']}"
            sentence_combinations.append([text, desc])

        cross_scores = cross_encoder.predict(sentence_combinations)
        for i, item in enumerate(candidates):
            item["rerank_score"] = float(cross_scores[i])

    # Caso C: SOLO IMAGEN
    elif image:
        query_vit_emb = get_vit_embedding(image)
        for item in candidates:
            idx = df.index[df['ProductId'] == item['ProductId']][0]
            vit_score = F.cosine_similarity(query_vit_emb, vit_embeddings[idx].unsqueeze(0)).item()
            item["rerank_score"] = float(vit_score)

    # RESULTADOS
    results = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)[:top_k]
    return results