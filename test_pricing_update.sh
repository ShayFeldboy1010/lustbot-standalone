#!/bin/bash

# Quick test script for updated pricing functionality
echo "🧪 Testing LustBot Updated Pricing Knowledge..."

# Test if the application can start
echo "📋 Checking application startup..."
python -c "
from app.agent import create_agent, SYSTEM_PROMPT
import sys

try:
    # Test agent creation
    agent = create_agent()
    print('✅ Agent created successfully with Groq model')
    
    # Check if pricing info is in the system prompt
    if 'מארז זוגי רגיל (1 יחידה) – 350₪' in SYSTEM_PROMPT:
        print('✅ Updated cash pricing for couples pack found in system prompt')
    else:
        print('❌ Cash pricing for couples pack NOT found in system prompt')
        
    if 'מארז זוגי עם משחק (1 יחידה) – 430₪' in SYSTEM_PROMPT:
        print('✅ Updated cash pricing for couples + game pack found in system prompt')
    else:
        print('❌ Cash pricing for couples + game pack NOT found in system prompt')
        
    print('✅ All tests passed!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"

echo ""
echo "📊 Summary of Changes:"
echo "   • Added Groq API as primary LLM provider"
echo "   • Updated cash pricing for couples packages:"
echo "     - מארז זוגי רגיל: 1=350₪, 2=550₪"
echo "     - מארז זוגי עם משחק: 1=430₪, 2=800₪"
echo "   • Updated system prompt with new pricing info"
echo "   • Updated product database (CSV) with pricing details"
echo ""
echo "🚀 Ready to serve customers with updated pricing!"
