import logging

logger = logging.getLogger(__name__)

def is_user_in_group(userid: str, groupid: str) -> bool:
    """
    Mock authorization function.
    In production, this would integrate with actual authorization service.
    """
    logger.debug(f"Checking if user {userid} is in group {groupid}")
    
    mock_user_groups = {
        "test@test.com": ["default", "admin", "mcp_users"],
        "user@example.com": ["default", "mcp_users"],
        "admin@example.com": ["default", "admin", "mcp_users", "super_admin"]
    }
    
    user_groups = mock_user_groups.get(userid, ["default"])
    is_authorized = groupid in user_groups
    
    logger.debug(f"User {userid} groups: {user_groups}, requested group: {groupid}, authorized: {is_authorized}")
    
    return is_authorized