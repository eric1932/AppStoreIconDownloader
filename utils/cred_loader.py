import os

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('API_KEY')
cse_id = os.getenv('CSE_ID')
