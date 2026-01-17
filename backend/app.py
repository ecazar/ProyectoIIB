from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from PIL import Image
import io
from google import genai

# Importar tus módulos
from backend.search_engine import search_query
from backend.ai_generation import get_response

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde el frontend

# Configurar Gemini
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyAZ0ThSbIGV0tzEiPHQmr_utDR7WXzu51Q")
gemini_client_api = genai.Client(api_key=api_key)


@app.route('/search', methods=['POST'])
def search():
    try:
        search_type = request.form.get('type')

        if search_type == 'image':
            # Búsqueda por imagen
            image_file = request.files.get('image')
            text_query = request.form.get('query', '')  # Texto adicional opcional

            if not image_file:
                return jsonify({'error': 'No se proporcionó una imagen'}), 400

            # Convertir la imagen a formato PIL
            image = Image.open(io.BytesIO(image_file.read()))

            # Buscar por imagen
            search_results = search_query(image, top_k=6)

            # Generar respuesta con IA si hay texto adicional
            if text_query:
                ai_explanation = _generate_combined_response(text_query, image, search_results)
            else:
                ai_explanation = f"Encontré {len(search_results)} productos similares a la imagen que subiste."

        else:
            # Búsqueda por texto
            text_query = request.form.get('query', '')

            if not text_query:
                return jsonify({'error': 'No se proporcionó una consulta'}), 400

            # Usar la función get_response que ya genera la explicación con IA
            response = get_response(text_query, gemini_client_api, top_k=6)
            search_results = response['results']
            ai_explanation = response['ai_explanation']

        # Formatear resultados para el frontend
        formatted_results = []
        for item in search_results:
            formatted_results.append({
                'ProductTitle': item.get('ProductTitle', 'Sin título'),
                'SubCategory': item.get('SubCategory', 'Sin categoría'),
                'Colour': item.get('Colour', 'Sin color'),
                'Usage': item.get('Usage', 'Sin uso especificado'),
                'ImageURL': item.get('ImageURL', ''),
                'rerank_score': f"{item.get('rerank_score', 0):.3f}"
            })

        return jsonify({
            'results': formatted_results,
            'ai_explanation': ai_explanation,
            'total': len(formatted_results)
        })

    except Exception as e:
        print(f"Error en /search: {str(e)}")
        return jsonify({'error': str(e)}), 500


def _generate_combined_response(text_query, image, results):
    """Genera respuesta cuando hay imagen + texto"""
    try:
        context_str = ""
        for i, r in enumerate(results):
            context_str += f"- Opción {i + 1}: {r['ProductTitle']} ({r['SubCategory']}, {r['Colour']})\n"

        prompt = f"""
        Actúa como un experto asistente de compras de moda.
        El usuario subió una imagen y agregó el siguiente comentario: "{text_query}".

        He encontrado los siguientes productos en nuestro catálogo (ordenados por relevancia):
        {context_str}

        Por favor, genera una respuesta breve (máximo 3 párrafos):
        1. Confirma lo que entendiste de la búsqueda.
        2. Destaca el producto #1 y explica por qué es la mejor coincidencia.
        3. Menciona una alternativa interesante de la lista.
        """

        response = gemini_client_api.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )

        return response.text if hasattr(response, 'text') else str(response)

    except Exception as e:
        return f"Encontré productos similares, pero no pude generar el análisis detallado. Error: {str(e)}"


@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint para mensajes de chat sin búsqueda"""
    try:
        data = request.get_json()
        message = data.get('message', '')

        if not message:
            return jsonify({'error': 'No se proporcionó un mensaje'}), 400

        # Aquí puedes agregar lógica adicional para el chatbot
        # Por ahora, devuelve un mensaje simple
        response_text = "¡Hola! Para buscar productos, escribe lo que buscas o sube una imagen. 😊"

        return jsonify({
            'response': response_text
        })

    except Exception as e:
        print(f"Error en /chat: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Endpoint para verificar que el servidor está funcionando"""
    return jsonify({'status': 'ok', 'message': 'Fashion Search API is running'})


if __name__ == '__main__':
    print("🚀 Iniciando Fashion Search API...")
    print("📡 Servidor corriendo en http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)