"""
Test configuration for KYC customer care bot
Contains hardcoded test data for easy testing
"""

# Hardcoded test phone number for automatic customer lookup
TEST_PHONE_NUMBER = "9812345680"  # Priya Yadav - Partial KYC case

# Alternative test numbers for different scenarios
TEST_SCENARIOS = {
    "full_kyc_within_timeline": "9812345670",  # Aarav Sharma - Full KYC, 30 days
    "partial_kyc": "9812345671",               # Diya Patel - Partial KYC
    "kyc_rejected": "9812345672",              # Arjun Singh - Rejected
    "full_kyc_overdue": "9812345680",          # Vivaan Das - Full KYC, beyond 30 days
    "default": "9812345675"                    # Priya Yadav - Partial KYC (good for general testing)
}


def get_test_phone_number():
    """Get the default test phone number for automatic lookup"""
    return TEST_PHONE_NUMBER

def get_test_customer_context():
    """Get context message for the test customer"""
    return f"Customer is calling from registered phone number: {TEST_PHONE_NUMBER}. PRIYA should greet them and immediately lookup their details to help with their KYC query."
