from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import tutorial  # , query
from app.api.routers import query_router

app = FastAPI(title="KT Assistant")

# Add CORS middleware BEFORE registering routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers (Authorization, Content-Type, etc.)
)

# Register your API routers
app.include_router(tutorial.router)
app.include_router(query_router.router)
# app.include_router(query.router)
