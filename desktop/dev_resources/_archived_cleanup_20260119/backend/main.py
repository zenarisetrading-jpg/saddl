from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes.executive_overview import router as executive_router

app = FastAPI(title="Saddle Executive Dashboard API")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(executive_router)

@app.get("/")
async def root():
    return {"message": "Saddle API is running"}
