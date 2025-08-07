# app/api/routers/tutorial.py
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from app.services import tutorial_service
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/tutorial", tags=["Tutorial"])

@router.post("/generate-stream")
async def generate_tutorial_stream(request: Request):
    body = await request.json()
    repo_url = body.get("repo_url")
    if not repo_url:
        return {"error": "repo_url is required"}

    return EventSourceResponse(tutorial_service.run_pipeline_streaming(repo_url))

@router.post("/get-tutorial")
async def get_existing_tutorial(request: Request):
    """
    Fetches the content of a pre-generated tutorial.
    """
    try:
        body = await request.json()
        repo_url = body.get("repo_url")
        if not repo_url:
            return JSONResponse(status_code=400, content={"error": "repo_url is required"})

        # Call the new service function to get the tutorial content
        tutorial_data = tutorial_service.fetch_existing_tutorial(repo_url)

        # The service function returns a dictionary with an 'error' key on failure
        if "error" in tutorial_data:
            return JSONResponse(status_code=404, content=tutorial_data)

        return JSONResponse(status_code=200, content=tutorial_data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"An unexpected error occurred: {e}"})


