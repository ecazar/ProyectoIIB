import kagglehub
import shutil
import os

# 1️⃣ Descargar dataset (queda en cache)
src_path = kagglehub.dataset_download("vikashrajluhaniwal/fashion-images")

# 2️⃣ Ruta destino EXACTA
dst_path = os.path.join(
    os.getcwd(),      # miproyecto
    "data",
    "fashion-images"
)

os.makedirs(dst_path, exist_ok=True)

# 3️⃣ Copiar todo el contenido
for item in os.listdir(src_path):
    src_item = os.path.join(src_path, item)
    dst_item = os.path.join(dst_path, item)

    if os.path.isdir(src_item):
        shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
    else:
        shutil.copy2(src_item, dst_item)

print("Dataset copiado en:", dst_path)
