from mcp.server.fastmcp import FastMCP
from settings import Settings
from user_repository import UserRepository
import logging
from settings import Settings
from llm_logger import log_error

settings = Settings()
logger = logging.getLogger("llm_logger")

MCP_PORT =  settings.MCP_SERVER_PORT
mcp = FastMCP("RBChat", port=MCP_PORT)


@mcp.tool()
async def count_items_in_database():
    """
    Retrieves the number of items in the database.

    Returns:
        A string representing the number of items in the database, or an error message.
    """
    try:
        print("Counting items in the database...")
        with UserRepository() as user_repo:
            count = user_repo.count_items()
        return str(count)
    except Exception as e:
        log_error(f"Failed to count items: {e}")
        return str(e)

@mcp.tool()
async def get_items_by_brand_and_category(brand: str, category: str) -> str:
    """
    Retrieves a list of items from the database specified by both brand and category.
    
    Args:
        brand: The brand name to filter items by.
        category: The category name to filter items by.
    
    Returns:
        A string representing the list of items from the specified brand and category, or an error message.
    """
    try:
        with UserRepository() as user_repo:
            items = user_repo.get_items_by_brand_and_category(brand, category)
        return str(items)
    except Exception as e:
        log_error(f"Failed to fetch items by brand and category: {e}")
        return f"Failed to fetch items by brand and category: {e}"

@mcp.tool()
async def get_items_by_brand(brand: str) -> str:
    """
    Retrieves a list of items from the database specified by the brand.
    
    Args:
        brand: The brand name to filter items by.
    
    Returns:
        A string representing the list of items from the specified brand, or an error message.
    """
    try:
        with UserRepository() as user_repo:
            items = user_repo.get_items_by_brand(brand)
        return str(items)
    except Exception as e:
        log_error(f"Failed to fetch items by brand: {e}")
        return f"Failed to fetch items by brand: {e}"

@mcp.tool()
async def get_items_by_category(category: str) -> str:
    """
    Retrieves a list of items from the database specified by the category.
    
    Args:
        category: The category name to filter items by.
    
    Returns:
        A string representing the list of items from the specified category, or an error message.
    """
    try:
        with UserRepository() as user_repo:
            items = user_repo.get_items_by_category(category)
        return str(items)
    except Exception as e:
        log_error(f"Failed to fetch items by category: {e}")
        return f"Failed to fetch items by category: {e}"

@mcp.tool()
async def get_items_by_name(name: str) -> str:
    """
    This tool is responsible for retrieving products by name. 
    
    Args:
        name: Name of the product or item. 
    
    Returns:
        A string representing the list of items from the specified name, or an error message.
    """
    try:
        with UserRepository() as user_repo:
            items = user_repo.get_items_by_name(name)
        return str(items)
    except Exception as e:
        log_error(f"Failed to fetch items by name: {e}")
        return f"Failed to fetch items by name and description: {e}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")