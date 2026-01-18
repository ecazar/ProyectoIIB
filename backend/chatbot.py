import os
from google import genai
from dotenv import load_dotenv
from backend.search_engine import search_query

load_dotenv()


class FashionChatbot:
    def __init__(self, search_engine=None):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Falta GEMINI_API_KEY")

        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"  # O el modelo que prefieras
        self.chat = self.client.chats.create(model=self.model_id)

    # funcion para procesar query en texto
    def process_query_text(self, user_input):
        # Determinar intención
        intent_prompt = f"Clasifica la intención de '{user_input}' en una palabra: BUSCAR o CHARLAR."
        intent_res = self.client.models.generate_content(model=self.model_id, contents=intent_prompt)
        intent = intent_res.text.strip().upper()
        if "CHARLAR" in intent:
            response = self.chat.send_message(user_input)
            return {"answer": response.text, "items": []}

        # Refinamiento Contextual
        refinement_prompt = f"Genera una frase de búsqueda super corta para busqueda en CLIP basada en '{user_input}' y lo que hablamos antes, solo dame la frase corta."
        print("prompt:" + refinement_prompt) # LOGGGGGGGGG!!!!!!!!!!!!!!!!!!!!!
        refined_query_res = self.chat.send_message(refinement_prompt)
        refined_query = refined_query_res.text.strip()
        print("query: " + refined_query)

        # Búsqueda y respuesta final
        results = search_query(text=refined_query,top_k=3)
        context = self._format_products_for_ai(results)
        final_response = self.chat.send_message(
            f"He encontrado esto para '{refined_query}': {context}. Actúa como Personal Shopper. Responde al usuario de forma natural confirmando los hallazgos."
        )

        return {"answer": final_response.text, "items": results}

    # funcion para procesar query en texto e imagenes
    def process_query_image(self, image, user_input=None):
        # Imagen + Texto
        if user_input:
            # Refinamiento Contextual
            refinement_prompt = f"Genera una frase de búsqueda super corta para busqueda en CLIP basada en '{user_input}' y lo que hablamos antes, solo dame la frase corta."
            print("prompt:" + refinement_prompt)
            refined_query_res = self.chat.send_message(refinement_prompt)
            refined_query = refined_query_res.text.strip()
            print("query: " + refined_query)

            # Búsqueda y respuesta final
            results = search_query(text=refined_query, image=image, top_k=3)
            context = self._format_products_for_ai(results)
            final_response = self.chat.send_message(
                f"He encontrado esto para '{refined_query}': {context}. Actúa como Personal Shopper. Responde al usuario de forma natural confirmando los hallazgos."
            )

        # Imagen
        else:
            # Búsqueda y respuesta final
            results = search_query(text=None, image=image, top_k=3)
            context = self._format_products_for_ai(results)
            final_response = self.chat.send_message(
                f"He encontrado esto para la imagen enviada: {context}. Actúa como Personal Shopper. Responde al usuario de forma natural confirmando los hallazgos."
            )
        return {"answer": final_response.text, "items": results}

    def _format_products_for_ai(self, results):
        formatted = ""
        # Usamos .get para evitar errores si falta alguna clave
        for r in results[:3]:
            formatted += f"- {r.get('ProductTitle', 'Producto')} (Color: {r.get('Colour', 'N/A')})\n"
            print(f"- {r.get('ProductTitle', 'Producto')} (Color: {r.get('Colour', 'N/A')}) id: {r.get('ProductId', 'Id')}\n")
        return formatted