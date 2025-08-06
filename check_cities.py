from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

try:
    response = client.from("cities").select("name").limit(10).execute()
    print("Cities found:", len(response.data))
    for city in response.data:
        print(" -", city["name"])
except Exception as e:
    print("Error:", e)