import os
from backend.search_engine import search_query
import google as genai

GENAI_MODEL_NAME = 'gemini-2.5-flash-lite'

def get_response(query, gemini_client_api, top_k=5):
    ai_response = ""
    results = search_query(query, top_k=5)

    if results:
        ai_response = _generate_gemini_summary(query, results, gemini_client_api)

    return {
        "results": results,
        "ai_explanation": ai_response
    }


def _generate_gemini_summary(query, results, gemini_client_api):
    """Generates the final explanation using the Gemini API"""
    try:
        # Convert image query to generic text for the prompt if needed
        query_text = query if isinstance(query, str) else "an image provided by the user"

        context_str = ""
        for i, r in enumerate(results):
            context_str += f"- Option {i + 1}: {r['ProductTitle']} ({r['SubCategory']}, {r['Colour']})\n"

        prompt = f"""
        Act as an expert fashion shopping assistant ("Fashion Stylist").
        The user searched for: "{query_text}".

        I have found the following products in our catalog (sorted by relevance):
        {context_str}

        Please generate a brief response (maximum 3 paragraphs):
        1. Confirm what you understood from the search.
        2. Highlight product #1 and explain why it is the best match.
        3. Mention an interesting alternative from the list.
        """

        response = gemini_client_api.models.generate_content(
            model = GENAI_MODEL_NAME,
            contents = prompt
        )
        return response

    except Exception as e:
        return f"I couldn't generate the AI analysis at this time. Error: {str(e)}"
