from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from backend.chatbot import FashionChatbot
# Importa tu motor de búsqueda real aquí
# from backend.search_engine import SearchEngine

app = FastAPI()

# PERMITIR CONEXIÓN DESDE EL FRONTEND
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializamos el Bot (ajusta según los parámetros de tu __init__)
# Si tu chatbot necesita el engine: bot = FashionChatbot(search_engine=SearchEngine())
bot = FashionChatbot(search_engine=None)

@app.post("/chat")  # <--- ESTA ES LA RUTA QUE EL SERVIDOR NO ENCONTRABA
async def chat_endpoint(message: str = Form(...)):
    print(f"Mensaje recibido: {message}") # Ver en consola si llega el texto
    try:
        response = bot.process_query(message)
        return response
    except Exception as e:
        print(f"Error procesando query: {e}")
        return {"answer": f"Error interno: {str(e)}", "items": []}

@app.post("/search-image")
async def image_endpoint(file: UploadFile = File(...), message: str = Form(None)):
    # Lógica temporal para que no de 404 al subir imagen
    return {"answer": "Búsqueda por imagen en desarrollo", "items": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)