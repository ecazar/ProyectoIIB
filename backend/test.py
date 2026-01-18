import os
import time

from google import genai
from backend.ai_generation import get_response

start = time.perf_counter()
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyAZ0ThSbIGV0tzEiPHQmr_utDR7WXzu51Q")
gemini_client_api = genai.Client(api_key=api_key)

print("Starting....")
results = get_response("nike gray shoes, chunky" , gemini_client_api,top_k=5)
print("finish....")
print(results)
end = time.perf_counter()
print(f"Tiempo total: {end - start:.2f} segundos")