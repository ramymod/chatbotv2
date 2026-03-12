from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from brain import GeminiBrain

app = FastAPI(title="Malaz API")
bot = GeminiBrain()

# Define the expected JSON payload using Pydantic
class ChatRequest(BaseModel):
    user_id: str = Field(default="guest")
    message: str

@app.get("/")
def health():
    return {"status": "healthy"}

@app.post("/chat")
def chat(request_data: ChatRequest):
    # Pydantic ensures 'message' exists, but we still check if it's an empty string
    if not request_data.message.strip():
        raise HTTPException(status_code=400, detail="No message provided")

    # Call Gemini 
    # (Note: If ask_gemini is an async function, you should use 'await' here 
    # and change 'def chat' to 'async def chat')
    reply = bot.ask_gemini(request_data.user_id, request_data.message)
    
    # FastAPI automatically converts dictionaries to JSON
    return {"reply": reply}

if __name__ == '__main__':
    print("Malaz running on Port 5000...")
    # uvicorn is the standard ASGI server used to run FastAPI apps
    uvicorn.run(app, host='0.0.0.0', port=5000)