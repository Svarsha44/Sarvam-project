import os
from dotenv import load_dotenv
from sarvamai import SarvamAI

# Load environment variables from .env
load_dotenv()

# Read the API key securely from environment
api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    raise ValueError("SARVAM_API_KEY not found in environment. Please check your .env file.")

# Initialize Sarvam AI client
client = SarvamAI(api_subscription_key=api_key)

# Query the Heritage Storytelling Agent
prompt = (
    "You are an Indic heritage and history scholar. "
    "Give me a fascinating, brief 2-sentence fact about the Lion Capital of Ashoka and its modern significance."
)

print("Connecting to Sarvam AI Chat Completion API (model: sarvam-105b-conversations)...")

response = client.chat.completions(
    model="sarvam-105b-conversations",
    messages=[
        {"role": "system", "content": "You are a knowledgeable Indic heritage, history, and mythology storyteller."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.5,
    max_tokens=300,
)

print("\n--- Heritage Storytelling Agent Response ---")
print(response.choices[0].message.content)
