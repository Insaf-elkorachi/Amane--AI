from dotenv import load_dotenv
import os

load_dotenv()

print("API =", os.getenv("OPENAI_API_KEY"))
print("MODEL =", os.getenv("OPENAI_MODEL"))