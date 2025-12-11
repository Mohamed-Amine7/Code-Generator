from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI()

# Autoriser l'origine localhost:3000 (React)
origins = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # permet l'origine de React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

intent_classifier = pipeline("text-classification", model="facebook/bart-large-mnli")

class InputText(BaseModel):
    text: str
    language: str

@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/analyze")
def analyze_text(payload: InputText):
    res = intent_classifier(payload.text)
    return {"intent": res}
