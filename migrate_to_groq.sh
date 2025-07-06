#!/bin/bash

# Migration script from OpenAI to Groq API
echo "🔄 Migrating LustBot from OpenAI to Groq API..."

# Install new requirements
echo "📦 Installing Groq SDK..."
pip install groq>=0.4.0

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your GROQ_API_KEY"
    echo "🔑 Get your Groq API key from: https://console.groq.com/keys"
else
    echo "✅ .env file exists"
    echo "⚠️  Make sure to add GROQ_API_KEY to your .env file"
    echo "🔑 Get your Groq API key from: https://console.groq.com/keys"
fi

echo ""
echo "🚀 Migration completed! Key changes:"
echo "   • Primary LLM: OpenAI → Groq (meta-llama/llama-4-scout-17b-16e-instruct)"
echo "   • Added groq>=0.4.0 to requirements.txt"
echo "   • Updated settings.py to use GROQ_API_KEY"
echo "   • Updated agent.py to use Groq model"
echo "   • OpenAI support remains for backward compatibility"
echo ""
echo "📋 Required environment variable:"
echo "   GROQ_API_KEY=your_groq_api_key_here"
echo "   GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct"
echo ""
echo "🏃 To run the application:"
echo "   make run-dev  # or python -m uvicorn app.main:app --reload --port 8001"
echo ""
echo "💡 Benefits of Groq with Llama 4 Scout:"
echo "   • 10x faster inference than OpenAI"
echo "   • Lower latency for better user experience"
echo "   • Cost-effective pricing"
echo "   • Latest Llama 4 Scout model with enhanced reasoning"
echo "   • Excellent Hebrew language support"
