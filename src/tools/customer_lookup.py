"""
Customer lookup tool for KYC Customer Care Bot.
Allows querying customer data by mobile number.
"""

import csv
import os
from typing import Dict, Any
from google.adk.tools import FunctionTool


def _get_data_file_path(data_file_path: str = "data/mock.csv") -> str:
    """Get the absolute path to the data file."""
    # Get the absolute path relative to the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, data_file_path)


def lookup_customer_by_opus_id(opus_id: str) -> Dict[str, Any]:
    """Look up customer information by Opus ID.
    
    Args:
        opus_id: The Opus ID to search for
        
    Returns:
        Dictionary containing customer information including name, email, mobile_number, 
        KYC status, and account status, or error message if not found.
    """
    try:
        # Clean the opus_id (remove any spaces, special characters, keep only digits)
        clean_opus_id = ''.join(filter(str.isdigit, opus_id))
        
        if not clean_opus_id:
            return {
                "success": False,
                "error": "Invalid Opus ID format. Please provide a valid Opus ID."
            }
        
        data_file = _get_data_file_path()
        
        if not os.path.exists(data_file):
            return {
                "success": False,
                "error": f"Customer data file not found at {data_file}"
            }
        
        # Search for the customer in the CSV file
        with open(data_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Check if Opus ID matches
                row_opus_id = ''.join(filter(str.isdigit, row.get('opus_id', '')))
                
                if row_opus_id == clean_opus_id:
                    # Found the customer, return the requested information
                    full_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
                    return {
                        "success": True,
                        "customer_found": True,
                        "message": f"Customer found with Opus ID {opus_id}: {full_name}",
                        "name": full_name,
                        "email": row.get('email', ''),
                        "opus_id": row.get('opus_id', ''),
                        "mobile_number": row.get('mobile_number', ''),
                        "kyc_status": row.get('kyc_status', ''),
                        "account_status": row.get('status', '')
                    }
            
            # Customer not found
            return {
                "success": True,
                "customer_found": False,
                "message": f"No customer found with Opus ID {opus_id}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error occurred while looking up customer by Opus ID: {str(e)}"
        }


def lookup_customer_by_mobile(mobile_number: str) -> Dict[str, Any]:
    """Look up customer information using their mobile number.
    
    Args:
        mobile_number: The mobile number to search for (10-digit number)
        
    Returns:
        Dictionary containing customer information including name, email, opus_id, 
        KYC status, and account status, or error message if not found.
    """
    try:
        # Clean the mobile number (remove any spaces, special characters)
        clean_mobile = ''.join(filter(str.isdigit, mobile_number))
        
        if len(clean_mobile) != 10:
            return {
                "success": False,
                "error": "Invalid mobile number format. Please provide a 10-digit mobile number."
            }
        
        data_file = _get_data_file_path()
        
        if not os.path.exists(data_file):
            return {
                "success": False,
                "error": f"Customer data file not found at {data_file}"
            }
        
        # Search for the customer in the CSV file
        with open(data_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Check if mobile number matches
                row_mobile = ''.join(filter(str.isdigit, row.get('mobile_number', '')))
                
                if row_mobile == clean_mobile:
                    # Found the customer, return the requested information
                    full_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
                    return {
                        "success": True,
                        "customer_found": True,
                        "message": f"Customer found: {full_name}",
                        "name": full_name,
                        "email": row.get('email', ''),
                        "opus_id": row.get('opus_id', ''),
                        "mobile_number": row.get('mobile_number', ''),
                        "kyc_status": row.get('kyc_status', ''),
                        "account_status": row.get('status', '')
                    }
            
            # Customer not found
            return {
                "success": True,
                "customer_found": False,
                "message": f"No customer found with mobile number {mobile_number}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error occurred while looking up customer: {str(e)}"
        }


# Create the FunctionTool instances
customer_lookup_tool = FunctionTool(func=lookup_customer_by_mobile)
customer_lookup_by_opus_id_tool = FunctionTool(func=lookup_customer_by_opus_id)
