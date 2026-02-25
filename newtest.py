import os

gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    print("✅ GEMINI_API_KEY detected!")
else:
    print("❌ GEMINI_API_KEY not found. Check your environment variables.")