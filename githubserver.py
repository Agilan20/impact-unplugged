from mcp.server.fastmcp import FastMCP
from fastmcp.tools import tool
import requests
import argparse

mcp = FastMCP(name="github-full-context")


GITHUB_RAW = "https://raw.githubusercontent.com"
API_TREE_URL = "https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"


# -----------------------------------------------------------
# TOOL: Fetch *all* files from GitHub repo
# -----------------------------------------------------------
@mcp.tool()
def load_github_repo_context(owner: str = "Agilan20", repo: str = "earmark-service", branch: str = "main"):
    """
    Returns ALL files and their contents from a GitHub repo.
    """
    owner = "Agilan20"
    repo = "earmark-service"
    branch = "main"
    # Step 1 — List all files using GitHub Tree API
    tree_url = API_TREE_URL.format(owner=owner, repo=repo, branch=branch)
    tree_res = requests.get(tree_url)

    if tree_res.status_code != 200:
        return f"Error fetching tree: {tree_res.status_code} - {tree_res.text}"

    tree_json = tree_res.json()

    if "tree" not in tree_json:
        return "Invalid GitHub Tree API response."

    files = [item for item in tree_json["tree"] if item["type"] == "blob"]

    print(files)


    repo_context = {}

    # Step 2 — Download contents of each file
    for file in files:
        path = file["path"]
        raw_url = f"{GITHUB_RAW}/{owner}/{repo}/{branch}/{path}"

        content_res = requests.get(raw_url)
        if content_res.status_code == 200:
            repo_context[path] = content_res.text
        else:
            repo_context[path] = f"<Failed to fetch: {content_res.status_code}>"

    return repo_context


# -----------------------------------------------------------
# TOOL: Summarize repository context (optional)
# -----------------------------------------------------------
@mcp.tool()
def summarize_repo_context(owner: str = "Agilan20", repo: str = "earmark-service", branch: str = "main", max_chars: int = 5000):
    """
    Loads entire repo and returns a compressed summary (truncated text).
    Useful for LLM context.
    """
    
    owner = "Agilan20"
    repo = "earmark-service"
    branch = "main"

    all_files = load_github_repo_context(owner, repo, branch)

    if isinstance(all_files, str):
        return all_files  # error string

    combined = "\n\n".join(
        f"# FILE: {path}\n{content}"
        for path, content in all_files.items()
    )

    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n... [TRUNCATED] ..."

    return combined


# -----------------------------------------------------------
# Run MCP server
# -----------------------------------------------------------
if __name__ == "__main__":
    print("🚀Starting server... ")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_type", type=str, default="sse", choices=["sse", "stdio"],
    )

    args = parser.parse_args()
    # Only pass server_type to run()
    mcp.run(args.server_type)