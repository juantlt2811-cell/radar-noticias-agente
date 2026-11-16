import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
for m in cliente.models.list():
    if "generateContent" in (m.supported_actions or []):
        print(m.name)
cliente.close()