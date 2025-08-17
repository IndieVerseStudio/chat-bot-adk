import csv
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class CustomerLookupTool:
    """Tool for looking up customer information and KYC status"""
    
    def __init__(self):
        self.data_file = os.path.join(os.path.dirname(__file__), '../../data/mock.csv')
        self.tickets_dir = os.path.join(os.path.dirname(__file__), '../../tickets')
        self.complaint_db = {}  # In-memory complaint storage for demo
        self.enquiry_db = {}    # In-memory enquiry storage for demo
        self.complaint_counter = 1000
        self.enquiry_counter = 2000
        
        # Ensure tickets directory exists
        os.makedirs(self.tickets_dir, exist_ok=True)
    
    def lookup_customer_by_phone(self, phone_number: str) -> Optional[Dict]:
        """Look up customer by phone number"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['mobile_number'] == phone_number:
                        return {
                            'id': row['id'],
                            'opus_id': row['opus_id'],
                            'first_name': row['first_name'],
                            'last_name': row['last_name'],
                            'mobile_number': row['mobile_number'],
                            'email': row['email'],
                            'status': row['status'],
                            'kyc_status': row['kyc_status'],
                            'is_aadhar_added': row['is_aadhar_added'].lower() == 'true',
                            'is_pan_added': row['is_pan_added'].lower() == 'true',
                            'is_bank_added': row['is_bank_added'].lower() == 'true',
                            'is_upi_added': row['is_upi_added'].lower() == 'true',
                            'data_created': int(row['data_created'])
                        }
                return None
        except Exception as e:
            print(f"Error reading customer data: {e}")
            return None
    
    def lookup_customer_by_opus_id(self, opus_id: str) -> Optional[Dict]:
        """Look up customer by Opus ID"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['opus_id'] == opus_id:
                        return {
                            'id': row['id'],
                            'opus_id': row['opus_id'],
                            'first_name': row['first_name'],
                            'last_name': row['last_name'],
                            'mobile_number': row['mobile_number'],
                            'email': row['email'],
                            'status': row['status'],
                            'kyc_status': row['kyc_status'],
                            'is_aadhar_added': row['is_aadhar_added'].lower() == 'true',
                            'is_pan_added': row['is_pan_added'].lower() == 'true',
                            'is_bank_added': row['is_bank_added'].lower() == 'true',
                            'is_upi_added': row['is_upi_added'].lower() == 'true',
                            'data_created': int(row['data_created'])
                        }
                return None
        except Exception as e:
            print(f"Error reading customer data: {e}")
            return None
    
    def get_multiple_accounts_by_phone(self, phone_number: str) -> List[Dict]:
        """Get all accounts registered with the same phone number"""
        accounts = []
        try:
            with open(self.data_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['mobile_number'] == phone_number:
                        accounts.append({
                            'opus_id': row['opus_id'],
                            'first_name': row['first_name'],
                            'last_name': row['last_name'],
                            'status': row['status'],
                            'kyc_status': row['kyc_status']
                        })
        except Exception as e:
            print(f"Error reading customer data: {e}")
        return accounts
    
    def check_kyc_completion_status(self, customer: Dict) -> Dict:
        """Check KYC completion status and calculate timeline"""
        kyc_status = customer['kyc_status']
        days_since_creation = customer['data_created']
        
        # Determine KYC completion level
        is_full_kyc = (customer['is_aadhar_added'] and 
                      customer['is_pan_added'] and 
                      customer['is_bank_added'])
        
        result = {
            'kyc_status': kyc_status,
            'is_full_kyc': is_full_kyc,
            'days_since_creation': days_since_creation,
            'is_within_30_days': days_since_creation <= 30,
            'days_remaining': max(0, 30 - days_since_creation) if days_since_creation <= 30 else 0,
            'days_overdue': max(0, days_since_creation - 30)
        }
        
        # Interpret status codes
        if kyc_status == 'F':
            result['status_description'] = 'Full KYC Complete'
        elif kyc_status == 'P':
            result['status_description'] = 'Partial KYC'
        elif kyc_status == 'N':
            result['status_description'] = 'No KYC'
        elif kyc_status == 'R':
            result['status_description'] = 'KYC Rejected'
        else:
            result['status_description'] = 'Unknown Status'
        
        return result
    
    def save_ticket_to_json(self, ticket: Dict, ticket_type: str) -> str:
        """Save ticket to JSON file and return file path"""
        ticket_id = ticket.get('complaint_id') or ticket.get('enquiry_id')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{ticket_type}_{ticket_id}_{timestamp}.json"
        filepath = os.path.join(self.tickets_dir, filename)
        
        # Add metadata
        ticket_with_metadata = {
            "ticket_id": ticket_id,
            "ticket_type": ticket_type,
            "created_timestamp": datetime.now().isoformat(),
            "created_by": "PRIYA - KYC Customer Care Bot",
            "ticket_data": ticket
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(ticket_with_metadata, f, indent=2, ensure_ascii=False)
            return filepath
        except Exception as e:
            print(f"Error saving ticket to JSON: {e}")
            return ""
    
    def check_existing_complaints(self, opus_id: str) -> List[Dict]:
        """Check for existing complaints for this customer"""
        complaints = []
        for complaint_id, complaint in self.complaint_db.items():
            if complaint['opus_id'] == opus_id:
                complaints.append(complaint)
        return complaints
    
    def create_complaint(self, customer: Dict, complaint_type: str, is_high_priority: bool = False) -> Dict:
        """Create a new complaint"""
        complaint_id = f"C{self.complaint_counter}"
        self.complaint_counter += 1
        
        complaint = {
            'complaint_id': complaint_id,
            'opus_id': customer['opus_id'],
            'customer_name': f"{customer['first_name']} {customer['last_name']}",
            'mobile_number': customer['mobile_number'],
            'type': 'Opus ID App',
            'sub_type': 'Painter/contractor Complaints',
            'issue': 'KYC Issue' if not is_high_priority else 'KYC Issue - Escalated',
            'subject': complaint_type,
            'priority': 'High' if is_high_priority else 'Standard',
            'timeline_days': 7,
            'status': 'Open',
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.complaint_db[complaint_id] = complaint
        
        # Save to JSON file
        json_path = self.save_ticket_to_json(complaint, "complaint")
        complaint['json_file_path'] = json_path
        
        return complaint
    
    def create_enquiry(self, customer: Dict, enquiry_type: str) -> Dict:
        """Create a new enquiry"""
        enquiry_id = f"E{self.enquiry_counter}"
        self.enquiry_counter += 1
        
        enquiry = {
            'enquiry_id': enquiry_id,
            'opus_id': customer['opus_id'],
            'customer_name': f"{customer['first_name']} {customer['last_name']}",
            'mobile_number': customer['mobile_number'],
            'type': 'General enquiries/Others',
            'sub_type': 'Other Enquiries',
            'enquiry': 'Opus Care',
            'issue': 'Become a Painter/Contractor',
            'subject': enquiry_type,
            'status': 'Open',
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.enquiry_db[enquiry_id] = enquiry
        
        # Save to JSON file
        json_path = self.save_ticket_to_json(enquiry, "enquiry")
        enquiry['json_file_path'] = json_path
        
        return enquiry

# Global instance for use by agent tools
customer_lookup_tool = CustomerLookupTool()
