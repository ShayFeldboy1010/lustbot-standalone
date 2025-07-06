#!/usr/bin/env python3
"""
Test script to verify Groq API configuration and model availability
"""

import sys
sys.path.append('/Users/shayFeldboy/Documents/shay/lustbot-standalone')

from app.settings import settings

try:
    # Test Groq import
    from groq import Groq as GroqClient
    print("✅ Groq SDK imported successfully")
    
    # Test API key
    client = GroqClient(api_key=settings.groq_api_key)
    print(f"✅ Groq client created with API key: {settings.groq_api_key[:20]}...")
    
    # Test model availability
    try:
        # Try to list available models
        models = client.models.list()
        print(f"✅ Connected to Groq API successfully")
        
        # Check if our specific model is available
        model_id = settings.groq_model
        available_models = [model.id for model in models.data]
        
        print(f"\n📋 Available models ({len(available_models)}):")
        for model in available_models[:10]:  # Show first 10
            print(f"   • {model}")
        
        if len(available_models) > 10:
            print(f"   ... and {len(available_models) - 10} more")
        
        if model_id in available_models:
            print(f"\n✅ Target model '{model_id}' is available!")
        else:
            print(f"\n⚠️  Target model '{model_id}' not found in available models")
            print("🔍 Suggested models for Hebrew/general chat:")
            suggested = [m for m in available_models if any(x in m.lower() for x in ['llama', 'chat', 'instruct'])]
            for model in suggested[:5]:
                print(f"   • {model}")
        
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        
    # Test a simple chat completion
    try:
        print(f"\n🧪 Testing chat completion with model: {settings.groq_model}")
        
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "user", "content": "שלום! תגיד משהו קצר בעברית."}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        if response.choices:
            content = response.choices[0].message.content
            print(f"✅ Model response: {content}")
        else:
            print("❌ No response content received")
            
    except Exception as e:
        print(f"❌ Error testing chat completion: {e}")
        if "model" in str(e).lower():
            print("💡 This might be a model availability issue. Try a different model ID.")
        
except ImportError as e:
    print(f"❌ Failed to import Groq: {e}")
    print("💡 Run: pip install groq>=0.4.0")
    
except Exception as e:
    print(f"❌ Configuration error: {e}")
    print("💡 Check your GROQ_API_KEY in .env file")

print(f"\n📊 Current configuration:")
print(f"   API Key: {settings.groq_api_key[:20]}...")
print(f"   Model: {settings.groq_model}")
print(f"   Temperature: {settings.agent_temperature}")
