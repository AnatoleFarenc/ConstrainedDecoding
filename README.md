Run the following commands:
export UV_CACHE_DIR="$PWD/.uv_cache"
export UV_LINK_MODE=copy
export HF_HOME="$PWD/.hf_cache"

Then set up the venv and download the dependencies:
uv venv
source .venv/bin/activate
uv sync

To run the program:
uv run python src/main.py