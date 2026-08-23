import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # โหลดค่าจาก .env

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="สวัสดี ช่วยแนะนำตัวสั้นๆ หน่อย"
)

print(response.text)