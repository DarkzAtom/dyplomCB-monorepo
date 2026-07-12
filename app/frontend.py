from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import retriever

# Import your existing setup
# Import your OpenAI client and Pinecone index

load_dotenv(dotenv_path=".env")
import openai

openai_apikey = os.getenv("OPENAI_APIKEY")
client = openai.OpenAI(api_key=openai_apikey)


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatMessage(BaseModel):
    message: str


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 6


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/chat.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/chat")
async def chat(msg: ChatMessage):
    try:
        # Use your existing OpenAI client
        response = retriever.process_user_query(msg.message)
        return {"response": response}

    except Exception as e:
        return {"response": f"Error: {str(e)}"}


@app.post("/api/retrieve")
async def api_retrieve(req: RetrieveRequest):
    """External data-retrieval endpoint (DYP-49): returns the raw retrieved
    articles for a query as JSON, without the chat-style LLM answer."""
    try:
        results = retriever.retrieve_articles(req.query, top_k=req.top_k)
        return {"query": req.query, "results": results}
    except Exception as e:
        return {"query": req.query, "results": [], "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("frontend:app", host="0.0.0.0", port=8000, reload=True)
