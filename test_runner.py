#!/usr/bin/env python3
"""
Test Runner for Priya KYC Bot

This script helps you quickly switch between test scenarios by updating 
the hardcoded phone number in the agent configuration.
"""

import json
import os
import sys
from pathlib import Path

def load_test_scenarios():
    """Load test scenarios from JSON file"""
    try:
        with open('test_scenarios.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: test_scenarios.json not found!")
        return None

def update_agent_phone_number(phone_number):
    """Update the hardcoded phone number in agent.py"""
    agent_file = Path("src/google_custom_agent/agent.py")
    
    if not agent_file.exists():
        print(f"Error: {agent_file} not found!")
        return False
    
    # Read the current file
    with open(agent_file, 'r') as f:
        content = f.read()
    
    # Find and replace the phone number
    old_pattern = "HARDCODED PHONE NUMBER: For this session, assume the customer is calling from phone number"
    new_content = content
    
    # Look for the pattern and replace the phone number
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if old_pattern in line:
            # Extract the current phone number and replace it
            parts = line.split('phone number ')
            if len(parts) > 1:
                # Keep everything before the phone number and add the new one
                prefix = parts[0] + 'phone number '
                # Remove any trailing period and add the new number
                lines[i] = prefix + phone_number + "."
                break
    
    new_content = '\n'.join(lines)
    
    # Write back to file
    with open(agent_file, 'w') as f:
        f.write(new_content)
    
    print(f"✓ Updated agent.py with phone number: {phone_number}")
    return True

def display_scenarios(scenarios_data):
    """Display available test scenarios"""
    print("\n" + "="*80)
    print("PRIYA KYC BOT - TEST SCENARIOS")
    print("="*80)
    
    scenarios = scenarios_data['test_scenarios']['scenarios']
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i:2d}. {scenario['name']} ({scenario['id']})")
        print(f"    Phone: {scenario['phone_number']}")
        print(f"    Customer: {scenario['customer_data']['name']} (Opus ID: {scenario['customer_data']['opus_id']})")
        print(f"    Description: {scenario['description']}")
        print(f"    Expected: {scenario['expected_outcome']}")

def display_customer_details(scenario):
    """Display detailed customer information for a scenario"""
    print("\n" + "-"*60)
    print("CUSTOMER DETAILS")
    print("-"*60)
    
    customer = scenario['customer_data']
    print(f"Name: {customer['name']}")
    print(f"Opus ID: {customer['opus_id']}")
    print(f"Phone: {scenario['phone_number']}")
    print(f"Status: {customer['status']}")
    print(f"KYC Status: {customer['kyc_status']}")
    print(f"Days since KYC: {customer['days_since_kyc']}")
    
    print(f"\nExpected Outcome: {scenario['expected_outcome']}")
    
    print(f"\nTest Phrases to Use:")
    for phrase in scenario['test_phrases']:
        print(f"  • \"{phrase}\"")
    
    print(f"\nExpected Workflow Path:")
    print(f"  {scenario['expected_path']}")

def main():
    """Main test runner function"""
    scenarios_data = load_test_scenarios()
    if not scenarios_data:
        return
    
    scenarios = scenarios_data['test_scenarios']['scenarios']
    
    while True:
        display_scenarios(scenarios_data)
        
        print(f"\n{'='*80}")
        print("Choose a test scenario (1-{}) or 'q' to quit: ".format(len(scenarios)), end='')
        
        choice = input().strip().lower()
        
        if choice == 'q':
            print("Goodbye!")
            break
        
        try:
            scenario_index = int(choice) - 1
            if 0 <= scenario_index < len(scenarios):
                scenario = scenarios[scenario_index]
                
                # Update agent with new phone number
                if update_agent_phone_number(scenario['phone_number']):
                    display_customer_details(scenario)
                    
                    print(f"\n{'='*60}")
                    print("READY TO TEST!")
                    print("="*60)
                    print("1. Restart your server: python src/main.py")
                    print("2. Open browser: https://localhost:8000")
                    print("3. Start conversation with Priya")
                    print("4. Use the test phrases provided above")
                    print("\nPress Enter to select another scenario...")
                    input()
                else:
                    print("Failed to update agent configuration!")
                    input("Press Enter to continue...")
            else:
                print("Invalid choice! Please select a number between 1 and {}.".format(len(scenarios)))
                input("Press Enter to continue...")
        except ValueError:
            print("Invalid input! Please enter a number or 'q' to quit.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
