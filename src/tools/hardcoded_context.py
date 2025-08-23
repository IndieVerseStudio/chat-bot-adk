"""
Hardcoded Context tool for KYC Customer Care Bot.
Provides predefined context about the caller's phone number.
"""

from typing import Dict, Any
from google.adk.tools import FunctionTool


def get_hardcoded_context() -> Dict[str, Any]:
    """Get hardcoded context including the caller's phone number.
    
    Returns:
        Dictionary containing predefined caller context information.
    """
    try:
        # Hardcoded phone number and related context
        HARDCODED_PHONE = "9812345769"  # Change this to your desired phone number
        
        # You can customize this context as needed
        context = {
            "success": True,
            "caller_phone": HARDCODED_PHONE,
            "is_registered_number": True,
            "context_message": f"Caller is calling from registered number {HARDCODED_PHONE}",
            "verification_status": "verified",
            "instructions": "Proceed with customer lookup using this phone number"
        }
        
        return context
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving hardcoded context: {str(e)}"
        }


def set_caller_context(phone_number: str) -> Dict[str, Any]:
    """Set caller context with a specific phone number.
    
    Args:
        phone_number: Phone number to set as context (optional, uses hardcoded if not provided)
        
    Returns:
        Dictionary containing caller context information.
    """
    try:
        # Use provided phone number (already has default value)
        context = {
            "success": True,
            "caller_phone": phone_number,
            "is_registered_number": True,
            "context_message": f"Setting caller context for phone number {phone_number}",
            "verification_status": "verified",
            "instructions": f"Use phone number {phone_number} for all subsequent customer lookups"
        }
        
        return context
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error setting caller context: {str(e)}"
        }


# Create the FunctionTool instances
hardcoded_context_tool = FunctionTool(func=get_hardcoded_context)
set_caller_context_tool = FunctionTool(func=set_caller_context)
