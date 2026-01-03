import os
from dotenv import load_dotenv

env_path = os.path.join("frontend", ".env")
print(f"Testing loading from: {os.path.abspath(env_path)}")

success = load_dotenv(env_path)
print(f"load_dotenv returned: {success}")

url = os.getenv("VITE_SUPABASE_URL")
print(f"VITE_SUPABASE_URL: '{url}'")

key = os.getenv("VITE_SUPABASE_ANON_KEY")
print(f"VITE_SUPABASE_ANON_KEY: '{key}' (masked: {key[:5]}...)")
