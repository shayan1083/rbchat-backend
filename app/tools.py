from mcp.server.fastmcp import FastMCP
from settings import Settings
from user_repository import UserRepository
import json

mcp = FastMCP("Math")

settings = Settings()

# calculate custom score to test mcp working
@mcp.tool()
def compute_custom_score(x: int, y: int, z: int) -> float:
    """
    Compute a custom weighted score using the formula:
    
    score = ((x * 2) + (y ** 1.5) - (z * 0.42)) / (x + y + z + 1)

    This score is used internally to rank experimental sensor data.
    """
    print("Computing custom score")
    score = ((x * 2) + (y ** 1.5) - (z * 0.42)) / (x + y + z + 1)
    rounded_score = round(score, 3)

    result = {
        "operation": "custom_score_calculation",
        "inputs": {"x": x, "y": y, "z": z},
        "score": rounded_score
    }

    return f"Custom score calculated successfully.\n\nResult: {json.dumps(result, indent=2)}"

# @mcp.tool()
# async def get_user_count() -> str:
#     """
#     Returns the total user count in the database
#     """
#     try:
#         user_repo = UserRepository(settings.DB_HOST, settings.DB_PORT, settings.DB_USER, settings.DB_PASSWORD, settings.DB_NAME)
#         user_repo.connect()
#         count = user_repo.get_user_count()
#         return str(count)
#     except Exception as e:
#         return f"Failed: {e}"
#     finally:
#         user_repo.close()

# @mcp.tool()
# async def list_users_from_api() -> str:
#     """
#     Returns a list of all users in the database.
#     """
#     try:
#         user_repo = UserRepository(settings.DB_HOST, settings.DB_PORT, settings.DB_USER, settings.DB_PASSWORD, settings.DB_NAME)
#         user_repo.connect()
#         users = user_repo.get_user_list()
#         return str(users)
#     except Exception as e:
#         return f"Error fetching user list: {e}"
#     finally:
#         user_repo.close()

# @mcp.tool()
# async def get_high_skill_users_via_api(skill: bool) -> str:
#     """
#     Retrieves a list of users who are either highly skilled or not, based on the input flag.
    
#     Args:
#         skill: Boolean value indicating whether to fetch highly skilled users (True) or not (False).
    
#     Returns:
#         A JSON string representing the list of matched users, or an error message.
#     """
#     try:
#         user_repo = UserRepository(settings.DB_HOST, settings.DB_PORT, settings.DB_USER, settings.DB_PASSWORD, settings.DB_NAME)
#         user_repo.connect()
#         users = user_repo.get_high_skill_users(skill)
#         return str(users)
#     except Exception as e:
#         return f"Failed to fetch from API: {e}"
#     finally:
#         user_repo.close()

@mcp.tool()
async def get_items_by_brand_and_category(brand: str, category: str) -> str:
    """
    Retrieves a list of items from the database specified by both brand and category.
    
    Args:
        brand: The brand name to filter items by.
        category: The category name to filter items by.
    
    Returns:
        A JSON string representing the list of items from the specified brand and category, or an error message.
    """
    try:
        user_repo = UserRepository(settings.DB_HOST, settings.DB_PORT, settings.DB_USER, settings.DB_PASSWORD, settings.DB_NAME)
        user_repo.connect()
        items = user_repo.get_items_by_brand_and_category(brand, category)
        return str(items)
    except Exception as e:
        return f"Failed to fetch items by brand and category: {e}"
    finally:
        user_repo.close()

@mcp.tool()
async def get_items_by_brand(brand: str) -> str:
    """
    Retrieves a list of items from the database specified by the brand.
    
    Args:
        brand: The brand name to filter items by.
    
    Returns:
        A JSON string representing the list of items from the specified brand, or an error message.
    """
    try:
        user_repo = UserRepository(settings.DB_HOST, settings.DB_PORT, settings.DB_USER, settings.DB_PASSWORD, settings.DB_NAME)
        user_repo.connect()
        items = user_repo.get_items_by_brand(brand)
        return str(items)
    except Exception as e:
        return f"Failed to fetch items by brand: {e}"
    finally:
        user_repo.close()

@mcp.tool()
async def get_items_by_category(category: str) -> str:
    """
    Retrieves a list of items from the database specified by the category.
    
    Args:
        category: The category name to filter items by.
    
    Returns:
        A JSON string representing the list of items from the specified category, or an error message.
    """
    try:
        user_repo = UserRepository(settings.DB_HOST, settings.DB_PORT, settings.DB_USER, settings.DB_PASSWORD, settings.DB_NAME)
        user_repo.connect()
        items = user_repo.get_items_by_category(category)
        return str(items)
    except Exception as e:
        return f"Failed to fetch items by category: {e}"
    finally:
        user_repo.close()





if __name__ == "__main__":
    mcp.run(transport="stdio")