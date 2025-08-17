# PRIYA - KYC Customer Care Bot Setup Guide

## Overview

PRIYA is a Google Speech Bot designed to handle KYC approval queries for Birla Opus contractors and painters. She follows the Enhanced KYC Approval workflow and provides automated customer support with local JSON ticket creation.

## Features

### ✅ **Implemented Features**

- **Phone Number Lookup**: Automatic customer lookup by phone number
- **KYC Status Checking**: Real-time KYC status validation and timeline calculation
- **Complaint Management**: Automatic creation of high-priority and standard complaints
- **Enquiry Creation**: Generation of enquiries for incomplete KYC cases
- **Workflow Adherence**: Follows the exact Enhanced KYC Approval workflow
- **Bilingual Support**: Hindi-English (Hinglish) conversation style
- **Automatic Processing**: No "please wait" messages - instant responses
- **JSON Ticket System**: Local ticket storage in JSON format with metadata
- **Named Agent**: PRIYA introduces herself by name for personal touch

### 🔧 **Technical Implementation**

- **Google ADK Integration**: Uses Google's Agent Development Kit for voice processing
- **Mock Database**: CSV-based customer data for testing
- **Real-time Tools**: 7 specialized tools for KYC workflow operations
- **WebSocket Communication**: Real-time bidirectional audio/text communication

## Testing the Bot

### 1. **Start the Application**

```bash
cd chat-bot-adk
python src/main.py
```

### 2. **Access the Interface**

- Open browser to: `https://localhost:8000`
- Accept the self-signed certificate warning

### 3. **Default Test Customer**

The bot is hardcoded to use this test customer profile:

| Phone Number | Customer Name | KYC Status      | Scenario                                 |
| ------------ | ------------- | --------------- | ---------------------------------------- |
| 9812345675   | Priya Yadav   | Partial KYC (P) | Should create enquiry for incomplete KYC |

**Available test scenarios in code:**

- `full_kyc_within_timeline`: 9812345670 (Aarav Sharma)
- `partial_kyc`: 9812345671 (Diya Patel)
- `kyc_rejected`: 9812345672 (Arjun Singh)
- `full_kyc_overdue`: 9812345680 (Vivaan Das)
- `default`: 9812345675 (Priya Yadav) - **Currently Active**

### 4. **Testing Workflow**

#### **Simple Testing Process**

1. Click "Start Voice Chat"
2. Say: "Hi" or "Hello" or mention KYC issues
3. **Expected**: PRIYA will automatically:
   - Greet you professionally ("My name is PRIYA")
   - Lookup Priya Yadav's details silently
   - Inform about partial KYC status
   - Create appropriate enquiry and save as JSON file
   - Provide next steps

#### **Test Phrases to Try**

- "Hi, my KYC approval is pending"
- "I want to know about my account approval"
- "My account is not approved yet"
- "When will my contractor account be ready?"

## Agent Behavior

### **Conversation Flow**

1. **Greeting**: "Namaste, welcome to Birla Opus. My name is PRIYA..."
2. **Automatic Lookup**: Instantly retrieves test customer details (Priya Yadav)
3. **Customer Identification**: Confirms customer name and details
4. **Status Assessment**: Evaluates KYC completion and timeline
5. **Action Taking**: Creates complaints/enquiries as needed and saves as JSON
6. **Solution Provision**: Provides next steps and timelines
7. **Closing**: Offers additional help and proper farewell

### **Key Phrases to Test**

- "Hi" or "Hello"
- "My KYC approval is pending"
- "Account approval issue"
- "Contractor registration problem"
- "When will my account be approved?"

## Tools Available to Agent

1. **`get_calling_customer_info`**: Automatic test customer lookup (Primary tool)
2. **`lookup_customer_details`**: Manual customer information retrieval
3. **`check_kyc_status_and_timeline`**: KYC status analysis
4. **`create_high_priority_complaint`**: Escalated issue handling
5. **`create_standard_complaint`**: Standard complaint creation
6. **`create_enquiry`**: Information request handling
7. **`get_complaint_status`**: Complaint tracking
8. **`validate_phone_number_for_lookup`**: Phone number verification

## Workflow Decision Logic

```
Customer Call → Phone Verification → Customer Lookup → KYC Status Check
                                                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    KYC Status Assessment                        │
├─────────────────────────────────────────────────────────────────┤
│ Full KYC (F) + Within 30 days    → Inform wait time           │
│ Full KYC (F) + Beyond 30 days    → Create complaint + TSM     │
│ Partial KYC (P) / No KYC (N)     → Guide completion + Enquiry │
│ Rejected KYC (R)                 → Resubmission guidance      │
└─────────────────────────────────────────────────────────────────┘
```

## Expected Agent Responses

### **Successful Lookup**

- Immediate greeting with customer name confirmation
- Automatic status explanation without wait prompts
- Clear next steps with timelines
- Appropriate complaint/enquiry creation

### **Error Handling**

- Customer not found: Request correct details
- Multiple accounts: Ask for specific Opus ID
- System errors: Graceful fallback responses

## JSON Ticket System

PRIYA automatically creates local JSON files for all tickets:

### **Ticket Storage Location**

- **Directory**: `tickets/` (created automatically)
- **Format**: `{type}_{ticket_id}_{timestamp}.json`
- **Example**: `complaint_C1000_20250117_175345.json`

### **JSON Ticket Structure**

```json
{
  "ticket_id": "C1000",
  "ticket_type": "complaint",
  "created_timestamp": "2025-01-17T17:53:45.123456",
  "created_by": "PRIYA - KYC Customer Care Bot",
  "ticket_data": {
    "complaint_id": "C1000",
    "opus_id": "100006",
    "customer_name": "Priya Yadav",
    "mobile_number": "9812345675",
    "type": "Opus ID App",
    "sub_type": "Painter/contractor Complaints",
    "issue": "KYC Issue",
    "subject": "Account Approval pending-Contractor",
    "priority": "Standard",
    "timeline_days": 7,
    "status": "Open",
    "created_date": "2025-01-17 17:53:45"
  }
}
```

### **Ticket Types**

- **Complaints**: High priority and standard complaints
- **Enquiries**: Information requests and guidance tickets

## Mock Data Structure

The `data/mock.csv` contains:

- **100 test customers** with varied KYC statuses
- **Different completion timelines** (25-35 days)
- **Multiple KYC completion levels** (Full, Partial, None, Rejected)
- **Realistic Indian names** and phone numbers

## Customization Options

### **Changing Test Customer**

To test different scenarios, modify `src/tools/test_config.py`:

```python
# Change this line to use different test scenarios
TEST_PHONE_NUMBER = "9812345670"  # Use any number from TEST_SCENARIOS
```

### **Adding New Customers**

Add rows to `data/mock.csv` with format:

```csv
id,opus_id,first_name,last_name,mobile_number,email,status,kyc_status,is_aadhar_added,is_pan_added,is_bank_added,is_upi_added,data_created
```

### **Modifying Responses**

Update instructions in `src/google_custom_agent/agent.py`:

- Greeting messages
- Error responses
- Workflow decision logic

### **Adding New Tools**

Create new tools in `src/tools/agent_tools.py` and add to agent configuration.

## Troubleshooting

### **Common Issues**

1. **SSL Certificate**: Accept browser warning for localhost
2. **Microphone Access**: Grant browser permissions
3. **Audio Issues**: Check system audio settings
4. **Tool Errors**: Verify CSV file accessibility

### **Debug Information**

- Check browser console for WebSocket messages
- Monitor server logs for tool execution
- Verify phone number format (10 digits)

## Architecture Notes

- **Frontend**: Vanilla JS with WebSocket for real-time communication
- **Backend**: FastAPI with Google ADK integration
- **Audio Processing**: PCM format with streaming buffers
- **Data Layer**: CSV-based mock database for testing
- **Agent Intelligence**: Gemini 2.5 Flash with native audio support

This setup provides a complete, testable KYC customer care bot that follows the exact workflow requirements and provides immediate, helpful responses to customer queries.
