
import os

env_content = """VITE_SUPABASE_URL=https://mxjntnzavvzcvrknipni.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_dkV6rhWURtYcg-Mn-150DQ_IeaOKxh2
"""

file_path = os.path.join("frontend", ".env")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(env_content)

print(f"Successfully wrote {file_path} with UTF-8 encoding.")
