# src/api/main.py

import os, sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from routers import queries

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(queries.router)
handler = Mangum(app)

if __name__ == "__main__":
    port = 8000
    print(f"Running the FastAPI server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)
