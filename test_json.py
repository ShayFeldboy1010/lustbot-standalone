#!/usr/bin/env python3
"""
Test script to validate the Google Sheets JSON credentials
"""
import json
import os

def test_json_from_env():
    """Test parsing JSON from environment variable"""
    print("Testing GOOGLE_APPLICATION_CREDENTIALS_JSON from environment...")
    
    json_content = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if not json_content:
        print("❌ Environment variable not found")
        return False
    
    print(f"✓ Environment variable found (length: {len(json_content)})")
    print(f"First 100 chars: {repr(json_content[:100])}")
    print(f"Last 100 chars: {repr(json_content[-100:])}")
    
    try:
        parsed = json.loads(json_content)
        print("✓ JSON is valid")
        print(f"Keys: {list(parsed.keys())}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"Error position: {e.pos if hasattr(e, 'pos') else 'N/A'}")
        if hasattr(e, 'pos') and e.pos:
            start = max(0, e.pos - 20)
            end = min(len(json_content), e.pos + 20)
            print(f"Content around error: {repr(json_content[start:end])}")
        return False

def test_json_from_file():
    """Test parsing JSON from file"""
    print("\nTesting JSON from file...")
    
    file_path = "creds/sheets.json"
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        print(f"✓ File found (length: {len(content)})")
        
        parsed = json.loads(content)
        print("✓ JSON is valid")
        print(f"Keys: {list(parsed.keys())}")
        return True
    except Exception as e:
        print(f"❌ Failed to parse file JSON: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Google Sheets JSON Validation Test")
    print("=" * 50)
    
    env_ok = test_json_from_env()
    file_ok = test_json_from_file()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Environment JSON: {'✓ OK' if env_ok else '❌ FAILED'}")
    print(f"File JSON: {'✓ OK' if file_ok else '❌ FAILED'}")
    
    if not env_ok and file_ok:
        print("\n💡 Recommendation: Copy file content to environment variable")
