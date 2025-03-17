import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.router import user, authentication, insights, algorithms, predict, profile

app = FastAPI()

origins = [ "*" ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(authentication.router)
app.include_router(insights.router)
app.include_router(algorithms.router)
app.include_router(predict.router)
app.include_router(profile.router)

@app.get("/")
def home():
    path = os.getcwd()
    x = path.replace("\\", "/")
    return {"data" : x}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=os.getenv("PORT", default=5000), log_level="info")