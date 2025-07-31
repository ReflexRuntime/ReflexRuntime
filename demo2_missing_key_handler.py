#!/usr/bin/env python3
"""
Demo 2: User Data Processor with Missing Key Self-Healing
========================================================

Shows ReflexRuntime automatically fixing missing key errors.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reflexruntime.core.orchestrator import activate_reflex_runtime

# Activate ReflexRuntime
activate_reflex_runtime(debug=False)

def get_user_email(user_data: dict) -> str:
    """Get user email - will self-heal missing keys."""
    return user_data['email']

def get_user_score(user_data: dict) -> int:
    """Calculate user score - will self-heal missing keys."""
    return user_data['posts'] * 2 + user_data['likes']

def main():
    """Demonstrate missing key self-healing."""
    print("👤 ReflexRuntime User Data Processor")
    print("=" * 50)
    print("Processing users with missing data fields...\n")
    
    # Test users - some missing required fields
    users = [
        {"name": "Alice", "email": "alice@test.com", "posts": 10, "likes": 50},
        {"name": "Bob", "posts": 5, "likes": 20},  # Missing email
        {"name": "Carol", "email": "carol@test.com"},  # Missing posts/likes
    ]
    
    for i, user in enumerate(users, 1):
        print(f"Processing User #{i}: {user['name']}")
        print(f"Data: {user}")
        
        # Try to get email - will self-heal if missing
        email = get_user_email(user)
        print(f"Email: {email}")
        
        # Try to calculate score - will self-heal if missing
        score = get_user_score(user)  
        print(f"Score: {score}")
        
        print("-" * 40)
    
    print("🎯 Demo complete! Notice how missing keys were handled automatically.")

if __name__ == "__main__":
    main() 