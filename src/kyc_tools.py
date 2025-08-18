"""
KYC Customer Data Query Tools for Priya Bot

This module provides tools for querying customer data and managing complaints/enquiries
according to the KYC approval workflow.
"""

import csv
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class CustomerData:
    """Customer data structure matching the CSV schema"""
    id: int
    opus_id: str
    first_name: str
    last_name: str
    mobile_number: str
    email: str
    status: str  # Y=Yes, P=Pending, R=Rejected, X=Expired, D=Disabled
    kyc_status: str  # F=Full, P=Partial, R=Rejected, N=No KYC
    is_aadhar_added: bool
    is_pan_added: bool
    is_bank_added: bool
    is_upi_added: bool
    data_created: int  # Days ago

@dataclass
class ComplaintData:
    """Complaint/Enquiry tracking structure"""
    complaint_id: str
    customer_id: int
    opus_id: str
    mobile_number: str
    type: str  # 'complaint' or 'enquiry'
    category: str
    sub_category: str
    issue: str
    subject: str
    status: str  # 'active', 'closed', 'escalated'
    created_date: datetime
    timeline_days: int
    priority: str  # 'normal', 'high'

class CustomerDataManager:
    """Manages customer data queries and business logic"""
    
    def __init__(self, data_file_path: str = None, complaints_file_path: str = None):
        if data_file_path is None:
            # Default to data/mock.csv relative to project root
            base_dir = Path(__file__).resolve().parent.parent
            data_file_path = base_dir / "data" / "mock.csv"
        
        if complaints_file_path is None:
            # Default to data/complaints.json relative to project root
            base_dir = Path(__file__).resolve().parent.parent
            complaints_file_path = base_dir / "data" / "complaints.json"
        
        self.data_file_path = data_file_path
        self.complaints_file_path = complaints_file_path
        self.customers = self._load_customer_data()
        self.complaints, self._complaint_counter = self._load_complaints_data()
    
    def _load_customer_data(self) -> Dict[str, CustomerData]:
        """Load customer data from CSV file"""
        customers = {}
        
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    customer = CustomerData(
                        id=int(row['id']),
                        opus_id=row['opus_id'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        mobile_number=row['mobile_number'],
                        email=row['email'],
                        status=row['status'],
                        kyc_status=row['kyc_status'],
                        is_aadhar_added=row['is_aadhar_added'].lower() == 'true',
                        is_pan_added=row['is_pan_added'].lower() == 'true',
                        is_bank_added=row['is_bank_added'].lower() == 'true',
                        is_upi_added=row['is_upi_added'].lower() == 'true',
                        data_created=int(row['data_created'])
                    )
                    customers[customer.mobile_number] = customer
        except FileNotFoundError:
            print(f"Warning: Customer data file not found at {self.data_file_path}")
        except Exception as e:
            print(f"Error loading customer data: {e}")
        
        return customers
    
    def _load_complaints_data(self) -> Tuple[Dict[str, ComplaintData], int]:
        """Load complaints data from JSON file"""
        complaints = {}
        complaint_counter = 1000
        
        try:
            if os.path.exists(self.complaints_file_path):
                with open(self.complaints_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    
                    # Load existing complaints
                    for complaint_id, complaint_dict in data.get('complaints', {}).items():
                        # Convert created_date string back to datetime
                        complaint_dict['created_date'] = datetime.fromisoformat(complaint_dict['created_date'])
                        complaints[complaint_id] = ComplaintData(**complaint_dict)
                    
                    # Load counter
                    complaint_counter = data.get('next_counter', 1000)
        except Exception as e:
            print(f"Warning: Could not load complaints data: {e}")
        
        return complaints, complaint_counter
    
    def _save_complaints_data(self):
        """Save complaints data to JSON file"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.complaints_file_path), exist_ok=True)
            
            # Prepare data for JSON serialization
            complaints_dict = {}
            for complaint_id, complaint in self.complaints.items():
                complaint_dict = asdict(complaint)
                # Convert datetime to string for JSON serialization
                complaint_dict['created_date'] = complaint.created_date.isoformat()
                complaints_dict[complaint_id] = complaint_dict
            
            data = {
                'complaints': complaints_dict,
                'next_counter': self._complaint_counter
            }
            
            with open(self.complaints_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
                
            print(f"✓ Complaints saved to {self.complaints_file_path}")
        except Exception as e:
            print(f"Error saving complaints data: {e}")
    
    def get_customer_by_phone(self, phone_number: str) -> Optional[CustomerData]:
        """Get customer data by phone number"""
        return self.customers.get(phone_number)
    
    def get_customer_by_opus_id(self, opus_id: str) -> Optional[CustomerData]:
        """Get customer data by Opus ID"""
        for customer in self.customers.values():
            if customer.opus_id == opus_id:
                return customer
        return None
    
    def get_customers_by_phone(self, phone_number: str) -> List[CustomerData]:
        """Get all customers associated with a phone number (for multiple accounts)"""
        # In this mock data, each phone has one account, but this handles the case
        customers = []
        for customer in self.customers.values():
            if customer.mobile_number == phone_number:
                customers.append(customer)
        return customers
    
    def calculate_kyc_days(self, customer: CustomerData) -> int:
        """Calculate days since KYC completion (using data_created as proxy)"""
        return customer.data_created
    
    def is_kyc_complete(self, customer: CustomerData) -> bool:
        """Check if KYC is fully complete"""
        return customer.kyc_status == 'F'
    
    def is_kyc_partial(self, customer: CustomerData) -> bool:
        """Check if KYC is partially complete"""
        return customer.kyc_status == 'P'
    
    def is_kyc_rejected(self, customer: CustomerData) -> bool:
        """Check if KYC is rejected"""
        return customer.kyc_status == 'R'
    
    def has_no_kyc(self, customer: CustomerData) -> bool:
        """Check if no KYC has been done"""
        return customer.kyc_status == 'N'
    
    def is_within_30_day_window(self, customer: CustomerData) -> bool:
        """Check if KYC completion is within 30-day processing window"""
        if not self.is_kyc_complete(customer):
            return False
        return self.calculate_kyc_days(customer) <= 30
    
    def get_remaining_days(self, customer: CustomerData) -> int:
        """Get remaining days in 30-day window"""
        if not self.is_kyc_complete(customer):
            return 0
        days_passed = self.calculate_kyc_days(customer)
        return max(0, 30 - days_passed)
    
    def check_existing_complaints(self, customer: CustomerData) -> List[ComplaintData]:
        """Check for existing complaints for a customer"""
        return [c for c in self.complaints.values() 
                if c.opus_id == customer.opus_id]
    
    def has_active_complaint(self, customer: CustomerData) -> bool:
        """Check if customer has any active complaints"""
        complaints = self.check_existing_complaints(customer)
        return any(c.status == 'active' for c in complaints)
    
    def get_active_complaint(self, customer: CustomerData) -> Optional[ComplaintData]:
        """Get the active complaint for a customer"""
        complaints = self.check_existing_complaints(customer)
        for complaint in complaints:
            if complaint.status == 'active':
                return complaint
        return None
    
    def create_complaint(self, customer: CustomerData, complaint_type: str, 
                        category: str, sub_category: str, issue: str, 
                        subject: str, priority: str = 'normal', 
                        timeline_days: int = 7) -> ComplaintData:
        """Create a new complaint"""
        complaint_id = f"PC{self._complaint_counter}"
        self._complaint_counter += 1
        
        complaint = ComplaintData(
            complaint_id=complaint_id,
            customer_id=customer.id,
            opus_id=customer.opus_id,
            mobile_number=customer.mobile_number,
            type=complaint_type,
            category=category,
            sub_category=sub_category,
            issue=issue,
            subject=subject,
            status='active',
            created_date=datetime.now(),
            timeline_days=timeline_days,
            priority=priority
        )
        
        self.complaints[complaint_id] = complaint
        self._save_complaints_data()  # Save to JSON file
        return complaint
    
    def create_enquiry(self, customer: CustomerData, enquiry_type: str,
                      sub_type: str, enquiry: str, issue: str, 
                      subject: str) -> ComplaintData:
        """Create a new enquiry"""
        enquiry_id = f"EN{self._complaint_counter}"
        self._complaint_counter += 1
        
        enquiry_data = ComplaintData(
            complaint_id=enquiry_id,
            customer_id=customer.id,
            opus_id=customer.opus_id,
            mobile_number=customer.mobile_number,
            type='enquiry',
            category=enquiry_type,
            sub_category=sub_type,
            issue=issue,
            subject=subject,
            status='active',
            created_date=datetime.now(),
            timeline_days=3,  # Standard enquiry timeline
            priority='normal'
        )
        
        self.complaints[enquiry_id] = enquiry_data
        self._save_complaints_data()  # Save to JSON file
        return enquiry_data

# Global instance
customer_data_manager = CustomerDataManager()

# Tool functions for the agent
def get_customer_by_phone(phone_number: str) -> Dict:
    """Tool function: Get customer data by phone number"""
    customer = customer_data_manager.get_customer_by_phone(phone_number)
    if customer:
        return {
            'found': True,
            'customer': {
                'id': customer.id,
                'opus_id': customer.opus_id,
                'name': f"{customer.first_name} {customer.last_name}",
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'mobile_number': customer.mobile_number,
                'email': customer.email,
                'status': customer.status,
                'kyc_status': customer.kyc_status,
                'kyc_complete': customer_data_manager.is_kyc_complete(customer),
                'kyc_partial': customer_data_manager.is_kyc_partial(customer),
                'kyc_rejected': customer_data_manager.is_kyc_rejected(customer),
                'no_kyc': customer_data_manager.has_no_kyc(customer),
                'days_since_kyc': customer_data_manager.calculate_kyc_days(customer),
                'within_30_days': customer_data_manager.is_within_30_day_window(customer),
                'remaining_days': customer_data_manager.get_remaining_days(customer),
                'documents': {
                    'aadhar': customer.is_aadhar_added,
                    'pan': customer.is_pan_added,
                    'bank': customer.is_bank_added,
                    'upi': customer.is_upi_added
                }
            }
        }
    return {'found': False, 'customer': None}

def get_customer_by_opus_id(opus_id: str) -> Dict:
    """Tool function: Get customer data by Opus ID"""
    customer = customer_data_manager.get_customer_by_opus_id(opus_id)
    if customer:
        return get_customer_by_phone(customer.mobile_number)
    return {'found': False, 'customer': None}

def check_multiple_accounts(phone_number: str) -> Dict:
    """Tool function: Check if phone number has multiple accounts"""
    customers = customer_data_manager.get_customers_by_phone(phone_number)
    return {
        'has_multiple': len(customers) > 1,
        'count': len(customers),
        'accounts': [{'opus_id': c.opus_id, 'name': f"{c.first_name} {c.last_name}"} 
                    for c in customers]
    }

def check_existing_complaints(opus_id: str) -> Dict:
    """Tool function: Check existing complaints for a customer"""
    customer = customer_data_manager.get_customer_by_opus_id(opus_id)
    if not customer:
        return {'found': False, 'complaints': []}
    
    complaints = customer_data_manager.check_existing_complaints(customer)
    return {
        'found': len(complaints) > 0,
        'has_active': customer_data_manager.has_active_complaint(customer),
        'complaints': [{
            'complaint_id': c.complaint_id,
            'type': c.type,
            'issue': c.issue,
            'subject': c.subject,
            'status': c.status,
            'created_date': c.created_date.strftime('%Y-%m-%d'),
            'timeline_days': c.timeline_days,
            'priority': c.priority
        } for c in complaints]
    }

def create_high_priority_complaint(opus_id: str) -> Dict:
    """Tool function: Create high priority complaint for KYC issue"""
    customer = customer_data_manager.get_customer_by_opus_id(opus_id)
    if not customer:
        return {'success': False, 'error': 'Customer not found'}
    
    complaint = customer_data_manager.create_complaint(
        customer=customer,
        complaint_type='complaint',
        category='Painter/contractor Complaints',
        sub_category='Opus ID App',
        issue='KYC Issue - Escalated',
        subject='Repeated complaint - Account Approval pending',
        priority='high',
        timeline_days=7
    )
    
    return {
        'success': True,
        'complaint_id': complaint.complaint_id,
        'timeline_days': complaint.timeline_days,
        'priority': complaint.priority
    }

def create_standard_complaint(opus_id: str) -> Dict:
    """Tool function: Create standard complaint for KYC issue"""
    customer = customer_data_manager.get_customer_by_opus_id(opus_id)
    if not customer:
        return {'success': False, 'error': 'Customer not found'}
    
    complaint = customer_data_manager.create_complaint(
        customer=customer,
        complaint_type='complaint',
        category='Painter/contractor Complaints',
        sub_category='Opus ID App',
        issue='KYC Issue',
        subject='Account Approval pending-Contractor',
        priority='normal',
        timeline_days=7
    )
    
    return {
        'success': True,
        'complaint_id': complaint.complaint_id,
        'timeline_days': complaint.timeline_days,
        'priority': complaint.priority
    }

def create_enquiry_partial_kyc(opus_id: str) -> Dict:
    """Tool function: Create enquiry for partial/no KYC"""
    customer = customer_data_manager.get_customer_by_opus_id(opus_id)
    if not customer:
        return {'success': False, 'error': 'Customer not found'}
    
    enquiry = customer_data_manager.create_enquiry(
        customer=customer,
        enquiry_type='General enquiries/Others',
        sub_type='Other Enquiries',
        enquiry='Opus Care',
        issue='Become a Painter/Contractor',
        subject='Partial KYC/No KYC-Contractor'
    )
    
    return {
        'success': True,
        'enquiry_id': enquiry.complaint_id,
        'timeline_days': enquiry.timeline_days
    }

def create_enquiry_within_window(opus_id: str) -> Dict:
    """Tool function: Create enquiry for within 30-day window"""
    customer = customer_data_manager.get_customer_by_opus_id(opus_id)
    if not customer:
        return {'success': False, 'error': 'Customer not found'}
    
    enquiry = customer_data_manager.create_enquiry(
        customer=customer,
        enquiry_type='General enquiries/Others',
        sub_type='Other Enquiries',
        enquiry='Opus Care',
        issue='Become a Painter/Contractor',
        subject='Account Approval pending-Contractor'
    )
    
    return {
        'success': True,
        'enquiry_id': enquiry.complaint_id,
        'timeline_days': enquiry.timeline_days,
        'note': 'Within 30-day window'
    }
