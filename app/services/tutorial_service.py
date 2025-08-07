# app/services/tutorial_service.py
import uuid
import os
import re
import glob
import asyncio
import logging
from typing import AsyncGenerator,Dict
from app.services.flow import create_tutorial_flow
from app.utils.logger_config import QueueHandler # Assuming you have this file

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DEFAULT_INCLUDE_PATTERNS = {
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
    "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "*Dockerfile",
    "*Makefile", "*.yaml", "*.yml",
}

DEFAULT_EXCLUDE_PATTERNS = {
    "assets/*", "data/*", "images/*", "public/*", "static/*", "temp/*",
    "*docs/*", "*venv/*", "*.venv/*", "*test*", "*tests/*", "*examples/*",
    "v1/*", "*dist/*", "*build/*", "*experimental/*", "*deprecated/*",
    "*misc/*", "*legacy/*", ".git/*", ".github/*", ".next/*", ".vscode/*",
    "*obj/*", "*bin/*", "*node_modules/*", "*.log"
}


# Helper function to get a clean repo name from a URL ---
def get_repo_name_from_url(url: str) -> str:
    """Extracts a clean, filesystem-friendly repository name from a git URL."""
    # Get the last part of the URL path
    repo_name = url.split('/')[-1]
    # Remove the .git extension if it exists
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    # Sanitize for filesystem: remove invalid characters
    repo_name = re.sub(r'[^\w\-_\.]', '_', repo_name)
    return repo_name


async def run_pipeline_streaming(repo_url: str) -> AsyncGenerator[str, None]:
    # Create a dedicated queue and logger for this request

    repo_name = get_repo_name_from_url(repo_url)

     # se absolute path for the output directory ---
    output_dir = os.path.join(PROJECT_ROOT, "tutorials", repo_name)

    if os.path.exists(output_dir):
        message = f"Tutorial for '{repo_name}' already exists. Use the /get-tutorial endpoint to retrieve it."
        logging.info(message)
        yield f"data: {message}\n\n"
        yield f"data: DONE\n\n"
        return

    os.makedirs(output_dir, exist_ok=True)

    queue: asyncio.Queue = asyncio.Queue()

    handler = QueueHandler(queue)
    # a simple formatter for clean log messages
    handler.setFormatter(logging.Formatter('%(message)s'))

    # Get a logger instance that is unique to avoid conflicts in a server environment
    # Using the run_id ensures each request gets its own isolated logger instance
    run_id = uuid.uuid4().hex[:6]
    logger = logging.getLogger(f"tutorial_logger_{run_id}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # Clear any existing handlers
    logger.addHandler(handler)
    logger.propagate = False # Prevent logs from bubbling up to the root logger

    #output_dir = f"tutorials/tutorial-{run_id}"
    #project_name = f"project-{run_id}"

    shared = {
        "repo_url": repo_url,
        "local_dir": None,
        "project_name": repo_name,
        "output_dir": output_dir,
        "include_patterns": DEFAULT_INCLUDE_PATTERNS,
        "exclude_patterns": DEFAULT_EXCLUDE_PATTERNS,
        "max_file_size": 500000, # Increased size for better analysis
        "language": "english",
        "use_cache": True,
        "max_abstraction_num": 10,
        "files": [],
        "abstractions": [],
        "relationships": {},
        "chapter_order": [],
        "chapters": [],
        "final_output_dir": None,
        "logger": logger # Pass the configured logger to the flow
    }

    async def run_flow():
        """The background task that runs the synchronous flow."""
        try:
            flow = create_tutorial_flow()
            # Run the blocking, synchronous function in a separate thread
            await asyncio.to_thread(flow.run, shared)
        finally:
            # Signal that the process is complete
            await queue.put("DONE")

    # Run the flow in a background task so it doesn't block our streaming loop
    asyncio.create_task(run_flow())

    # This loop runs immediately, waiting for messages to appear on the queue
    while True:
        message = await queue.get()
        if message == "DONE":
            break
        # Yield the log message in SSE format
        yield f"data: {message.strip()}\n\n"

    # Send a final message to let the client know it's truly finished
    yield f"data: DONE\n\n"


    
# --- NEW: Function to fetch content of an existing tutorial ---
def fetch_existing_tutorial(repo_url: str) -> Dict:
    """
    Finds and reads all chapters of an existing tutorial.

    Returns a dictionary with the tutorial content or an error message.
    """
    repo_name = get_repo_name_from_url(repo_url)
    #output_dir = f"tutorials/tutorial-6fd862/project-6fd862"
      # --- MODIFICATION: Use absolute path for the output directory ---
    output_dir = os.path.join(PROJECT_ROOT, "tutorials", repo_name)

    if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
        return {"error": f"Tutorial for repository '{repo_name}' not found."}

    # Find all markdown files in the directory. This is more robust than
    # assuming a specific subdirectory structure.
    # The user's example `tutorials\tutorial-...\project-...\*.md` suggests a nested
    # structure. `glob` with `recursive=True` can handle this.
    # We will search for the first directory inside `output_dir` if it exists.
    
    # Let's search for .md files in the output_dir and its subdirectories
    search_path = os.path.join(output_dir, '**', '*.md')
    md_files = glob.glob(search_path, recursive=True)

    if not md_files:
        return {"error": f"Tutorial directory for '{repo_name}' exists but contains no chapter (.md) files."}

    chapters = {}
    # Sort files to maintain chapter order (e.g., 01_, 02_, etc.)
    for file_path in sorted(md_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Create a clean chapter title from the filename
            filename = os.path.basename(file_path)
            # 1. Remove number prefix like '01_'
            title = re.sub(r'^\d+_', '', filename)
            # 2. Remove extension and replace underscores
            title = title.replace('.md', '').replace('_', ' ').strip()
            # 3. Capitalize the first letter or use title case
            title = title.capitalize() if len(title.split()) == 1 else title.title()

            chapters[title] = content
        except Exception as e:
            logging.error(f"Error reading or processing file {file_path}: {e}")
            chapters[os.path.basename(file_path)] = f"Error reading this chapter: {e}"

    return {"repo_url": repo_url, "chapters": chapters}