"""
Google ADK Tools Wrapper for KYC Customer Data Management

This module wraps the KYC tools to make them compatible with Google ADK's tool system.
"""

from google.adk.tools import FunctionTool
import sys
import os

# Add the parent directory to the path to import kyc_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kyc_tools import (
    get_customer_by_phone,
    get_customer_by_opus_id, 
    check_multiple_accounts,
    check_existing_complaints,
    create_high_priority_complaint,
    create_standard_complaint,
    create_enquiry_partial_kyc,
    create_enquiry_within_window
)

# Create ADK-compatible tools using FunctionTool
def customer_lookup_by_phone_func(phone_number: str):
    """Look up customer information using their phone number. Returns customer details including KYC status, account status, and processing timeline information."""
    return get_customer_by_phone(phone_number)

def customer_lookup_by_opus_id_func(opus_id: str):
    """Look up customer information using their Opus ID. Use this when customer provides their Opus ID for verification."""
    return get_customer_by_opus_id(opus_id)

def check_multiple_accounts_func(phone_number: str):
    """Check if a phone number is associated with multiple customer accounts. Use this to determine if you need to ask for specific Opus ID."""
    return check_multiple_accounts(phone_number)

def check_existing_complaints_func(opus_id: str):
    """Check if customer has any existing complaints or enquiries in the system. Use this to determine if they have active complaints before creating new ones."""
    return check_existing_complaints(opus_id)

def create_high_priority_complaint_func(opus_id: str):
    """Create a high priority complaint for customers with repeated KYC approval issues. Use this when customer has had previous complaints that were closed or timeline exceeded."""
    return create_high_priority_complaint(opus_id)

def create_standard_complaint_func(opus_id: str):
    """Create a standard complaint for KYC approval issues when customer's KYC is complete but beyond 30-day window."""
    return create_standard_complaint(opus_id)

def create_partial_kyc_enquiry_func(opus_id: str):
    """Create an enquiry for customers with partial or no KYC completion. Use this when customer needs to complete their KYC documentation."""
    return create_enquiry_partial_kyc(opus_id)

def create_within_window_enquiry_func(opus_id: str):
    """Create an enquiry for customers whose KYC is complete but still within the 30-day processing window."""
    return create_enquiry_within_window(opus_id)

# Wrap functions in FunctionTool
customer_lookup_by_phone = FunctionTool(func=customer_lookup_by_phone_func)
customer_lookup_by_opus_id = FunctionTool(func=customer_lookup_by_opus_id_func)
check_multiple_accounts_tool = FunctionTool(func=check_multiple_accounts_func)
check_complaints_tool = FunctionTool(func=check_existing_complaints_func)
create_high_priority_complaint_tool = FunctionTool(func=create_high_priority_complaint_func)
create_standard_complaint_tool = FunctionTool(func=create_standard_complaint_func)
create_partial_kyc_enquiry_tool = FunctionTool(func=create_partial_kyc_enquiry_func)
create_within_window_enquiry_tool = FunctionTool(func=create_within_window_enquiry_func)

# List of all KYC tools for easy import
kyc_tools = [
    customer_lookup_by_phone,
    customer_lookup_by_opus_id,
    check_multiple_accounts_tool, 
    check_complaints_tool,
    create_high_priority_complaint_tool,
    create_standard_complaint_tool,
    create_partial_kyc_enquiry_tool,
    create_within_window_enquiry_tool
]
