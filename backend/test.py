import torch
from PIL import Image
import io
from backend.search_engine import search_query


def print_results(title, results):
    """Función auxiliar para imprimir resultados de forma bonita"""
    print(f"\n{'=' * 50}")
    print(f"🔍 {title.upper()}")
    print(f"{'=' * 50}")

    if not results:
        print("❌ No se encontraron resultados.")
        return

    for i, res in enumerate(results, 1):
        print(f"{i}. [{res['ProductId']}] {res['ProductTitle']}")
        print(f"   📊 Score Final (Rerank): {res['rerank_score']:.4f}")
        print("-" * 30)


def run_tests():
    print("🚀 Iniciando Mesa de Pruebas del Motor de Búsqueda...")

    try:
        # --- TEST 1: Solo Texto ---
        query_text = "green shoes"
        # --------------------------
        print(f"\nProbando búsqueda por texto: '{query_text}'")
        results_text = search_query(text=query_text, image=None, top_k=3)
        print_results("Resultado: Solo Texto", results_text)

        # --- TEST 2: Solo Imagen ---
        # Asegúrate de tener una imagen de prueba en tu carpeta
        image_path = "test_image.jpeg"  # <--- Cambia esto por una ruta real
        try:
            test_img = Image.open(image_path)
            print(f"\nProbando búsqueda por imagen: '{image_path}'")
            results_img = search_query(text=None, image=test_img, top_k=3)
            print_results("Resultado: Solo Imagen", results_img)

            # --- TEST 3: Búsqueda Híbrida ---
            hybrid_text = "but in red color"
            print(f"\nProbando búsqueda Híbrida: Imagen + '{hybrid_text}'")
            results_hybrid = search_query(text=hybrid_text, image=test_img, top_k=3)
            print_results("Resultado: Híbrida (Imagen + Texto)", results_hybrid)

        except FileNotFoundError:
            print(f"\n⚠️ Saltando pruebas de imagen: No se encontró '{image_path}'")

    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_tests()