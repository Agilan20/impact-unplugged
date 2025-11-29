from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

@mcp.tool()
def add(a: int, b: int) -> int:
    """
    _summary_
    Add two numbers together
    """
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """
    _summary_
    Multiply two numbers together
    """
    return a * b


if __name__ == "__main__":
    mcp.run(transport="stdio")
