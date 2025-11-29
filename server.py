from mcp.server.fastmcp import FastMCP
import argparse
mcp = FastMCP("Weather")
github_mcp = FastMCP("GitHub API")

@mcp.tool(name="get_weather", description="Get the weather for a city")
async def get_weather(city: str) -> str:
    """
    _summary_
    Get the weather for a city
    """
    print("---------Hit-----------")
    return f"The weather in {city} is sunny"

if __name__ == "__main__":
    print("🚀Starting server... ")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_type", type=str, default="sse", choices=["sse", "stdio"],
    )

    args = parser.parse_args()
    # Only pass server_type to run()
    mcp.run(args.server_type)