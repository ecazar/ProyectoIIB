from sentence_transformers import SentenceTransformer, CrossEncoder, util
import torch
import torch.nn.functional as F
from backend.preprocess_data import get_vit_embedding, clip_model
from backend.preprocess_data import load_data

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')


def search_query(text=None, image=None, top_k=5):
    assert text is not None or image is not None, "Debes pasar texto, imagen o ambos"

    df, clip_embeddings, vit_embeddings = load_data()

    # -------------------------
    # 1️⃣ RETRIEVAL con CLIP
    # -------------------------
    initial_k = 30
    scores = []

    if text is not None:
        text_emb = clip_model.encode(text, convert_to_tensor=True)
        text_scores = util.cos_sim(text_emb, clip_embeddings)[0]
        scores.append(text_scores)

    if image is not None:
        image_emb = clip_model.encode(image, convert_to_tensor=True)
        image_scores = util.cos_sim(image_emb, clip_embeddings)[0]
        scores.append(image_scores)

    # Combinar scores (promedio)
    combined_scores = torch.stack(scores).mean(dim=0)
    top_results = torch.topk(combined_scores, k=initial_k)

    candidates = []
    for score, idx in zip(top_results.values, top_results.indices):
        item = df.iloc[int(idx)].to_dict()
        item["clip_score"] = float(score)
        candidates.append(item)

    # -------------------------
    # 2️⃣ RERANKING
    # -------------------------
    # Precalcular embedding de imagen si existe
    if image is not None:
        query_vit_emb = get_vit_embedding(image)

    # Texto + Imagen
    if text is not None and image is not None:
        sentence_combinations = []

        for item in candidates:
            product_desc = (
                f"{item['ProductTitle']}. "
                f"Category: {item['SubCategory']}. "
                f"Color: {item['Colour']}. "
                f"Usage: {item['Usage']}"
            )
            sentence_combinations.append([text, product_desc])

        cross_scores = cross_encoder.predict(sentence_combinations)

        for i, item in enumerate(candidates):
            idx = df.index[df['ProductId'] == item['ProductId']][0]
            vit_score = F.cosine_similarity(
                query_vit_emb,
                vit_embeddings[idx].unsqueeze(0)
            ).item()

            # ⚖️ Score híbrido
            item["rerank_score"] = 0.6 * cross_scores[i] + 0.4 * vit_score

    # Solo TEXTO
    elif text is not None:
        sentence_combinations = []

        for item in candidates:
            product_desc = (
                f"{item['ProductTitle']}. "
                f"Category: {item['SubCategory']}. "
                f"Color: {item['Colour']}. "
                f"Usage: {item['Usage']}"
            )
            sentence_combinations.append([text, product_desc])

        cross_scores = cross_encoder.predict(sentence_combinations)

        for i, item in enumerate(candidates):
            item["rerank_score"] = float(cross_scores[i])

    # Solo IMAGEN
    else:
        for item in candidates:
            idx = df.index[df['ProductId'] == item['ProductId']][0]
            vit_score = F.cosine_similarity(
                query_vit_emb,
                vit_embeddings[idx].unsqueeze(0)
            ).item()
            item["rerank_score"] = vit_score

    # -------------------------
    # 3️⃣ RESULTADOS FINALES
    # -------------------------
    results = sorted(
        candidates,
        key=lambda x: x["rerank_score"],
        reverse=True
    )[:top_k]

    return results
