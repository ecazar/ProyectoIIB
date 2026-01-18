import os
from google import genai
from dotenv import load_dotenv
from backend.search_engine import search_query

load_dotenv()


class FashionChatbot:
    def __init__(self, search_engine):
        """
        search_engine: Instancia de la clase SearchEngine para realizar búsquedas
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Falta GEMINI_API_KEY")

        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash-lite"

        self.chat = self.client.chats.create(model=self.model_id)

    def process_query(self, user_input, current_results=None):
        """
        Procesa el texto del usuario, decide si necesita buscar y genera la respuesta.
        """

        # 1. Determinar la intención: ¿Es charla o es una búsqueda/filtro?
        intent_prompt = f"""
        Analiza el mensaje: "{user_input}"
        Clasifica la intención en una sola palabra:
        - "BUSCAR": Si pide productos, colores, tallas o cambios sobre lo anterior.
        - "CHARLAR": Si es un saludo, despedida, agradecimiento o comentario irrelevante a productos.
        """
        intent_res = self.client.models.generate_content(
            model=self.model_id,
            contents=intent_prompt
        )
        intent = intent_res.text.strip().upper()

        # Si solo es charla, respondemos amablemente sin buscar
        if "CHARLAR" in intent:
            response = self.chat.send_message(user_input)
            return {
                "answer": response.text,
                "items": current_results if current_results else []
            }

        # 2. Si es BUSCAR, refinamos la consulta usando la memoria
        # Esto permite que "pero en azul" se convierta en "Zapatos Nike en azul"
        refinement_prompt = f"""
        Mensaje del usuario: "{user_input}"
        Basado en el historial, genera una frase de búsqueda optimizada para un motor CLIP.
        No respondas al usuario, solo devuelve la frase de búsqueda.
        """
        refined_res = self.chat.send_message(refinement_prompt)
        refined_query = refined_res.text.strip()

        # 3. Realizar la búsqueda real con el SearchEngine (CLIP + Re-ranking)
        # Nota: El engine ya devuelve los resultados ordenados por el Cross-Encoder
        new_results = search_query(refined_query)

        # 4. Generar la respuesta final "humana" con los resultados
        context = self._format_products_for_ai(new_results)
        final_prompt = f"""
        El usuario dijo: "{user_input}"
        He encontrado estos productos en el catálogo:
        {context}

        Responde al usuario como un experto personal shopper. 
        Explica brevemente por qué el primer resultado es el ideal.
        """
        final_res = self.chat.send_message(final_prompt)

        return {
            "answer": final_res.text,
            "items": new_results
        }

    def generate_visual_analysis(self, results):
        """
        Genera un comentario cuando el usuario sube una imagen.
        """
        if not results:
            return "He analizado tu imagen, pero no encontré productos similares en el catálogo."

        context = self._format_products_for_ai(results)
        prompt = f"""
        El usuario ha subido una foto para buscar algo similar.
        Estos son los productos más parecidos que encontramos:
        {context}

        Actúa como estilista y comenta brevemente qué similitudes encontraste (estilo, color o forma).
        """
        response = self.model.generate_content(prompt)
        return response.text

    def _format_products_for_ai(self, results):
        """Helper para convertir la lista de dicts en texto para el prompt"""
        formatted = ""
        for i, r in enumerate(results[:3]):  # Solo pasamos los top 3 para no saturar el prompt
            formatted += f"- {r['ProductTitle']} (Color: {r['Colour']}, Uso: {r['Usage']}, Relevancia: {r['rerank_score']})\n"
        return formatted

