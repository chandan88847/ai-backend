import uuid
import os
import re
import glob
import asyncio
import logging
import shutil
from typing import AsyncGenerator, Dict, DefaultDict
from collections import defaultdict
from app.services.flow import create_tutorial_flow
from app.utils.logger_config import QueueHandler # Assuming you have this file

# --- Globals and Constants ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# This dictionary is shared across all requests to hold a unique lock for each repo.
REPO_GENERATION_LOCKS: DefaultDict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

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

# --- Helper Function ---
def get_repo_name_from_url(url: str) -> str:
    """Extracts a clean, filesystem-friendly repository name from a git URL."""
    repo_name = url.split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    repo_name = re.sub(r'[^\w\-_\.]', '_', repo_name)
    return repo_name

# --- Main Service Functions ---
async def run_pipeline_streaming(repo_url: str) -> AsyncGenerator[str, None]:
    """
    Generates a tutorial from a repository URL, ensuring concurrency safety
    and proper state management for completed or failed runs.
    """
    repo_name = get_repo_name_from_url(repo_url)
    output_dir = os.path.join(PROJECT_ROOT, "tutorials", repo_name)
    completion_marker = os.path.join(output_dir, "_SUCCESS")

    # Acquire a lock specific to this repository to prevent race conditions.
    async with REPO_GENERATION_LOCKS[repo_name]:
        # First, check if a complete tutorial already exists.
        if os.path.exists(completion_marker):
            message = f"Tutorial for '{repo_name}' has already been successfully generated."
            yield f"data: {message}\n\n"
            yield f"data: DONE\n\n"
            return
        
        # If no success marker, check if an incomplete directory exists from a failed run.
        if os.path.isdir(output_dir):
            logging.warning(f"Found incomplete tutorial for '{repo_name}'. Cleaning up before retry.")
            # Safely delete the old directory and all its contents.
            shutil.rmtree(output_dir)

        # We are now clear to create a new directory for this generation attempt.
        os.makedirs(output_dir, exist_ok=True)
    
    # The lock is released. The initial setup is done. Now, start the heavy lifting.
    
    # --- Per-request setup for isolated logging ---
    queue: asyncio.Queue = asyncio.Queue()
    handler = QueueHandler(queue)
    handler.setFormatter(logging.Formatter('%(message)s'))

    run_id = uuid.uuid4().hex[:6]
    logger = logging.getLogger(f"tutorial_logger_{run_id}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    shared = {
        "repo_url": repo_url_val,
        "local_dir": local_dir_val,
        "project_name": repo_name,
        "output_dir": output_dir,
        "include_patterns": DEFAULT_INCLUDE_PATTERNS,
        "exclude_patterns": DEFAULT_EXCLUDE_PATTERNS,
        "max_file_size": 500000,
        "language": "english",
        "use_cache": True,
        "max_abstraction_num": 10,
        "files": [],
        "abstractions": [],
        "relationships": {},
        "chapter_order": [],
        "chapters": [],
        "final_output_dir": None,
        "logger": logger
    }

    async def run_flow():
        """Wrapper to run the synchronous flow and handle completion status."""
        try:
            flow = create_tutorial_flow()
            await asyncio.to_thread(flow.run, shared)

            # CRITICAL STEP: Create the marker file only after the flow completes successfully.
            with open(completion_marker, "w") as f:
                f.write("completed")
            
            logger.info("Tutorial generation successful. Completion marker created.")

        except Exception as e:
            logger.error(f"TUTORIAL GENERATION FAILED for {repo_name}: {e}", exc_info=True)
            # The incomplete directory will be cleaned up by the next run attempt.
        finally:
            await queue.put("DONE")

    asyncio.create_task(run_flow())

    while True:
        message = await queue.get()
        if message == "DONE":
            break
        yield f"data: {message.strip()}\n\n"

    yield f"data: DONE\n\n"


def fetch_existing_tutorial(repo_url: str) -> Dict:
    """
    Safely fetches a pre-generated tutorial, ensuring it's complete
    by checking for the _SUCCESS marker file.
    """
    repo_name = get_repo_name_from_url(repo_url)
    output_dir = os.path.join(PROJECT_ROOT, "tutorials", repo_name)
    completion_marker = os.path.join(output_dir, "_SUCCESS")

    if not os.path.exists(completion_marker):
        return {"error": f"A complete tutorial for '{repo_name}' was not found. It may be generating or a previous attempt may have failed."}
    
    search_path = os.path.join(output_dir, '**', '*.md')
    md_files = glob.glob(search_path, recursive=True)

    if not md_files:
        return {"error": f"Tutorial for '{repo_name}' is marked as complete but contains no chapter (.md) files."}

    chapters = {}
    for file_path in sorted(md_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            filename = os.path.basename(file_path)
            title = re.sub(r'^\d+_', '', filename)
            title = title.replace('.md', '').replace('_', ' ').strip().title()
            chapters[title] = content
        except Exception as e:
            logging.error(f"Error reading chapter file {file_path}: {e}")
            chapters[os.path.basename(file_path)] = f"Error reading this chapter: {e}"

    return {"repo_url": repo_url, "chapters": chapters}