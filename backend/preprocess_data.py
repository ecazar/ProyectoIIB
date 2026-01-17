import pandas as pd
import requests
from PIL import Image
import torch
import os
import logging
from tqdm import tqdm
from io import BytesIO
import pickle
from sentence_transformers import SentenceTransformer
from transformers import ViTImageProcessor, ViTModel

# Configuración de Rutas
DATA_PATH = "data/fashion.csv"
CLIP_CACHE = "data/clip_embeddings.pkl"
VIT_CACHE = "data/vit_embeddings.pkl"
CLEAN_DF_PATH = "data/cleaned_data.pkl"

BATCH_SIZE = 32

CLIP_MODEL_NAME = 'clip-ViT-B-32'
VIT_MODEL_NAME = 'google/vit-base-patch16-224'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Inicializar modelos
clip_model = SentenceTransformer(CLIP_MODEL_NAME)
vit_processor = ViTImageProcessor.from_pretrained(VIT_MODEL_NAME)
vit_model = ViTModel.from_pretrained(VIT_MODEL_NAME)

def download_image(url: str) -> Image.Image:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")

def get_vit_embedding(image):
    inputs = vit_processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = vit_model(**inputs)
    return outputs.pooler_output  # Vector de 768 dimensiones

def load_data():
    logger.info("Loading dataset...")
    df = pd.read_csv(DATA_PATH, on_bad_lines='skip')
    df = df.dropna(subset=['ImageURL']).reset_index(drop=True)

    if not (os.path.exists(CLIP_CACHE) and os.path.exists(VIT_CACHE)):
        logger.info("Cache not found. Processing catalog...")
        process_catalog()
    else:
        logger.info("Cache found. Loading embeddings...")

    with open(CLIP_CACHE, "rb") as f:
        clip_embeddings = pickle.load(f)
    with open(VIT_CACHE, "rb") as f:
        vit_embeddings = pickle.load(f)

    logger.info("Data loaded successfully.")
    return df, clip_embeddings, vit_embeddings

def process_catalog():
    logger.info("Starting catalog processing...")

    df = pd.read_csv(DATA_PATH, on_bad_lines='skip')
    df = df.dropna(subset=['ImageURL']).reset_index(drop=True)

    clip_vectors = []
    vit_vectors = []
    valid_indices = []

    images_batch = []
    indices_batch = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Downloading images"):
        try:
            img = download_image(row["ImageURL"])
            images_batch.append(img)
            indices_batch.append(idx)

            if len(images_batch) == BATCH_SIZE:
                _process_batch(
                    images_batch,
                    indices_batch,
                    clip_vectors,
                    vit_vectors,
                    valid_indices
                )
                images_batch.clear()
                indices_batch.clear()
        except Exception as e:
            logger.warning(f"Image failed idx={idx}: {e}")

    if images_batch:
        _process_batch(
            images_batch,
            indices_batch,
            clip_vectors,
            vit_vectors,
            valid_indices
        )
    logger.info("Saving cache files...")
    cleaned_df = df.loc[valid_indices].reset_index(drop=True)

    with open(CLIP_CACHE, "wb") as f:
        pickle.dump(torch.cat(clip_vectors), f)

    with open(VIT_CACHE, "wb") as f:
        pickle.dump(torch.cat(vit_vectors), f)

    with open(CLEAN_DF_PATH, "wb") as f:
        pickle.dump(cleaned_df, f)

    logger.info("Catalog processing completed successfully.")

def _process_batch(images, indices, clip_vectors, vit_vectors, valid_indices):
    # CLIP embeddings (batch real)
    clip_embs = clip_model.encode(
        images,
        batch_size=len(images),
        convert_to_tensor=True,
        show_progress_bar=False
    )

    # ViT embeddings (batch real)
    vit_embs = get_vit_embedding(images)

    clip_vectors.append(clip_embs)
    vit_vectors.append(vit_embs)
    valid_indices.extend(indices)