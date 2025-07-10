#!/usr/bin/env python3

import ast
import json

# Simulate the problematic data from extraction
extracted_data = {
    'cuisine_types': "['Health Store']",  # String representation of list
    'features': "[]",  # Empty list as string
    'recent_reviews': "[]"  # Empty list as string
}

print("🐛 CURRENT PROBLEMATIC LOGIC:")
print("=" * 50)

for field_name, field_value in extracted_data.items():
    print(f"\nField: {field_name}")
    print(f"Value: {field_value}")
    print(f"Type: {type(field_value)}")
    print(f"isinstance(value, list): {isinstance(field_value, list)}")
    
    # Current broken logic
    if not isinstance(field_value, list):
        result = [field_value] if field_value else []
        print(f"❌ Current logic result: {result}")
        print(f"❌ Result type: {type(result)}")
    else:
        print(f"✅ Already a list: {field_value}")

print("\n" + "=" * 50)
print("🔧 FIXED LOGIC:")
print("=" * 50)

def convert_to_list(value):
    """Convert various formats to proper list"""
    if isinstance(value, list):
        return value
    
    if isinstance(value, str):
        # Try to parse as JSON/Python literal
        if value.strip() in ['[]', '']:
            return []
        
        try:
            # Try JSON first
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        
        try:
            # Try Python literal evaluation
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed
        except (ValueError, SyntaxError):
            pass
        
        # If all parsing fails, treat as single item
        return [value] if value.strip() else []
    
    # For other types, convert to single-item list if not empty
    return [value] if value else []

for field_name, field_value in extracted_data.items():
    print(f"\nField: {field_name}")
    print(f"Original: {field_value} (type: {type(field_value)})")
    result = convert_to_list(field_value)
    print(f"✅ Fixed result: {result}")
    print(f"✅ Result type: {type(result)}")
    if result:
        print(f"✅ First item type: {type(result[0])}") 