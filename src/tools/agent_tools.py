from typing import Dict, List, Optional
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from customer_lookup import customer_lookup_tool
from test_config import get_test_phone_number, get_test_customer_context

def get_calling_customer_info() -> Dict:
    """
    Get information about the customer who is currently calling.
    This automatically uses the test phone number for lookup.
    Use this tool first when a customer starts speaking to get their details.
    
    Returns:
        Dictionary containing customer details including name, KYC status, and timeline information
    """
    test_phone = get_test_phone_number()
    return lookup_customer_details(phone_number=test_phone)

def lookup_customer_details(phone_number: str = "", opus_id: str = "") -> Dict:
    """
    Look up customer details by phone number or Opus ID.
    Use this tool when customer provides their phone number or Opus ID for verification.
    
    Args:
        phone_number: Customer's registered mobile number
        opus_id: Customer's Opus ID for verification
        
    Returns:
        Dictionary containing customer details including name, KYC status, and timeline information
    """
    if phone_number:
        customer = customer_lookup_tool.lookup_customer_by_phone(phone_number)
    elif opus_id:
        customer = customer_lookup_tool.lookup_customer_by_opus_id(opus_id)
    else:
        return {"error": "Either phone_number or opus_id must be provided"}
    
    if not customer:
        return {"error": "Customer not found", "found": False}
    
    # Check for multiple accounts with same phone number
    multiple_accounts = customer_lookup_tool.get_multiple_accounts_by_phone(customer['mobile_number'])
    
    # Get KYC status details
    kyc_details = customer_lookup_tool.check_kyc_completion_status(customer)
    
    # Check existing complaints
    existing_complaints = customer_lookup_tool.check_existing_complaints(customer['opus_id'])
    
    result = {
        "found": True,
        "customer": customer,
        "multiple_accounts": len(multiple_accounts) > 1,
        "all_accounts": multiple_accounts if len(multiple_accounts) > 1 else [],
        "kyc_details": kyc_details,
        "existing_complaints": existing_complaints,
        "has_active_complaints": len(existing_complaints) > 0
    }
    
    return result

def check_kyc_status_and_timeline(opus_id: str) -> Dict:
    """
    Check detailed KYC status and calculate timeline for account approval.
    Use this tool to get comprehensive KYC information for decision making.
    
    Args:
        opus_id: Customer's Opus ID
        
    Returns:
        Dictionary with KYC status, completion level, and timeline calculations
    """
    customer = customer_lookup_tool.lookup_customer_by_opus_id(opus_id)
    if not customer:
        return {"error": "Customer not found"}
    
    kyc_details = customer_lookup_tool.check_kyc_completion_status(customer)
    
    # Determine next action based on status
    if kyc_details['kyc_status'] == 'F':  # Full KYC
        if kyc_details['is_within_30_days']:
            action = "wait_within_timeline"
            message = f"KYC complete. Please wait {kyc_details['days_remaining']} more days."
        else:
            action = "escalate_overdue"
            message = f"KYC complete but {kyc_details['days_overdue']} days overdue. Needs escalation."
    elif kyc_details['kyc_status'] in ['P', 'N']:  # Partial or No KYC
        action = "complete_kyc_first"
        message = "Please complete KYC documentation first, then wait 30 days."
    elif kyc_details['kyc_status'] == 'R':  # Rejected
        action = "kyc_rejected"
        message = "KYC has been rejected. Please resubmit correct documents."
    else:
        action = "unknown_status"
        message = "Unknown KYC status. Please contact support."
    
    return {
        "customer_name": f"{customer['first_name']} {customer['last_name']}",
        "kyc_details": kyc_details,
        "recommended_action": action,
        "message": message
    }

def create_high_priority_complaint(opus_id: str, reason: str = "Repeated complaint - Account Approval pending") -> Dict:
    """
    Create a high priority complaint for escalated KYC issues.
    Use this when customer has previous complaints or KYC is overdue beyond 30 days.
    
    Args:
        opus_id: Customer's Opus ID
        reason: Reason for the complaint
        
    Returns:
        Dictionary with complaint details including complaint number and timeline
    """
    customer = customer_lookup_tool.lookup_customer_by_opus_id(opus_id)
    if not customer:
        return {"error": "Customer not found"}
    
    complaint = customer_lookup_tool.create_complaint(customer, reason, is_high_priority=True)
    
    return {
        "success": True,
        "complaint_number": complaint['complaint_id'],
        "customer_name": complaint['customer_name'],
        "priority": complaint['priority'],
        "timeline_days": complaint['timeline_days'],
        "created_date": complaint['created_date'],
        "json_file_saved": complaint.get('json_file_path', ''),
        "sms_sent": True,
        "message": f"High priority complaint {complaint['complaint_id']} created and saved to JSON file. Timeline: {complaint['timeline_days']} days."
    }

def create_standard_complaint(opus_id: str, reason: str = "Account Approval pending-Contractor") -> Dict:
    """
    Create a standard complaint for KYC approval issues.
    Use this when KYC is complete but beyond 30 days and no previous complaints exist.
    
    Args:
        opus_id: Customer's Opus ID
        reason: Reason for the complaint
        
    Returns:
        Dictionary with complaint details including complaint number and timeline
    """
    customer = customer_lookup_tool.lookup_customer_by_opus_id(opus_id)
    if not customer:
        return {"error": "Customer not found"}
    
    complaint = customer_lookup_tool.create_complaint(customer, reason, is_high_priority=False)
    
    return {
        "success": True,
        "complaint_number": complaint['complaint_id'],
        "customer_name": complaint['customer_name'],
        "priority": complaint['priority'],
        "timeline_days": complaint['timeline_days'],
        "created_date": complaint['created_date'],
        "json_file_saved": complaint.get('json_file_path', ''),
        "sms_sent": True,
        "message": f"Standard complaint {complaint['complaint_id']} created and saved to JSON file. Timeline: {complaint['timeline_days']} days."
    }

def create_enquiry(opus_id: str, enquiry_type: str) -> Dict:
    """
    Create an enquiry for KYC-related questions.
    Use this when customer needs guidance but doesn't require a complaint.
    
    Args:
        opus_id: Customer's Opus ID
        enquiry_type: Type of enquiry (e.g., "Partial KYC/No KYC-Contractor", "Account Approval pending-Contractor")
        
    Returns:
        Dictionary with enquiry details including enquiry number
    """
    customer = customer_lookup_tool.lookup_customer_by_opus_id(opus_id)
    if not customer:
        return {"error": "Customer not found"}
    
    enquiry = customer_lookup_tool.create_enquiry(customer, enquiry_type)
    
    return {
        "success": True,
        "enquiry_number": enquiry['enquiry_id'],
        "customer_name": enquiry['customer_name'],
        "type": enquiry['subject'],
        "created_date": enquiry['created_date'],
        "json_file_saved": enquiry.get('json_file_path', ''),
        "message": f"Enquiry {enquiry['enquiry_id']} created and saved to JSON file successfully."
    }

def get_complaint_status(complaint_id: str) -> Dict:
    """
    Check the status of an existing complaint.
    Use this to provide updates on previously raised complaints.
    
    Args:
        complaint_id: The complaint ID to check
        
    Returns:
        Dictionary with complaint status and timeline information
    """
    if complaint_id in customer_lookup_tool.complaint_db:
        complaint = customer_lookup_tool.complaint_db[complaint_id]
        return {
            "found": True,
            "complaint_id": complaint['complaint_id'],
            "status": complaint['status'],
            "priority": complaint['priority'],
            "timeline_days": complaint['timeline_days'],
            "created_date": complaint['created_date'],
            "customer_name": complaint['customer_name']
        }
    else:
        return {"found": False, "error": "Complaint not found"}

def validate_phone_number_for_lookup(phone_number: str) -> Dict:
    """
    Validate if the provided phone number can be used for customer lookup.
    Use this when customer calls from a different number than registered.
    
    Args:
        phone_number: Phone number to validate
        
    Returns:
        Dictionary indicating if number is valid for lookup and any multiple accounts
    """
    accounts = customer_lookup_tool.get_multiple_accounts_by_phone(phone_number)
    
    if not accounts:
        return {
            "valid": False,
            "message": "No accounts found with this phone number. Please provide Opus ID for verification."
        }
    elif len(accounts) == 1:
        return {
            "valid": True,
            "single_account": True,
            "account": accounts[0],
            "message": f"Account found for {accounts[0]['first_name']} {accounts[0]['last_name']}"
        }
    else:
        return {
            "valid": True,
            "single_account": False,
            "multiple_accounts": accounts,
            "message": f"Multiple accounts found ({len(accounts)} accounts). Please provide specific Opus ID."
        }
