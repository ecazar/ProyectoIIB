from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.chatbot import FashionChatbot
from backend.search_engine import search_query
from PIL import Image
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializamos el Bot
bot = FashionChatbot(search_engine=search_query)

# Post para procesar texto
@app.post("/chat")
async def chat_endpoint(message: str = Form(...)):
    try:
        print("estoy en chat")
        return bot.process_query_text(message)
    except Exception as e:
        return {"answer": f"Error: {str(e)}", "items": []}

# Post para procesar imagenes
@app.post("/search-image")
async def search_image_endpoint(
        file: UploadFile = File(...),
        message: str = Form(None)
):
    try:
        image_bytes = await file.read()
        pil_image = Image.open(io.BytesIO(image_bytes))

        # 1. Búsqueda (Tu lógica actual)
        if message and message.strip():
            print(f"🔍 Búsqueda Híbrida: '{message}' + Imagen")
            return bot.process_query_image(image=pil_image, user_input=message)
        else:
            print("🖼️ Búsqueda Solo Imagen")
            return bot.process_query_image(image=pil_image, user_input=None)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)