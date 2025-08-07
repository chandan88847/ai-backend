The Idea 
KT Assist : AI-Powered Developer Onboarding

To run Backend Pyhton application

Prerequisties
Python pacakage installed (ours current version 3.13.5 ) 

To install dependencies
pip install -r requirements.txt

To run 
uvicorn app.main:app --reload
or
uvicorn app.main:app --reload --port 8000

running in this port
http://localhost:8000/docs


api enpoints details available in postman collection 
https://.postman.co/workspace/My-Workspace~dc8c98dd-7db9-432b-852b-6a1b2833cdd6/collection/38206943-5e1ed9c4-628f-476a-95ea-af6f6a6e3383?action=share&creator=38206943

also available in swagger default docs
http://localhost:8000/docs


File Structure excpected
dxp-kt-assist-ai/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Entry point (uvicorn app.main:app)
│   ├── config.py                # Environment config (env vars, paths)
│   ├── api/                     # --- API Layer ---
│   │   ├── __init__.py
│   │   ├── routers/             # Route groups
│   │   │   ├── __init__.py
│   │   │   ├── tutorial.py      # /tutorial endpoint
│   │   │   └── query.py         # /query endpoint
│   │   └── controllers/         # Controller = request handler
│   │       ├── __init__.py
│   │       ├── tutorial_controller.py
│   │       └── query_controller.py
│   ├── services/                # --- Business Logic Layer ---
│   │   ├── __init__.py
│   │   ├── tutorial_service.py  # Clone repo, run Pocket-Flow
│   │   ├── query_service.py     # Semantic search + LLM call
│   |   ├── flow.py             # DAG builder
|   |   └── nodes.py            # All flow Nodes (FetchRepo, etc)
|   |        
│   ├── repositories/            # --- DB, file, vector access ---
│   │   ├── __init__.py
│   │   └── vector_repo.py       # Chroma / Pinecone / Weaviate
│   ├── llm/                     # --- LLM interaction utils ---
│   │   ├── __init__.py
│   │   ├── call_llm.py
│   │   └── embedder.py
│ 
│                 
│
├── tests/
│   ├── __init__.py
│   ├── test_tutorial.py
│   └── test_query.py
│
├── .env                         # Environment variables
├── requirements.txt             # Python dependencies
├── README.md

