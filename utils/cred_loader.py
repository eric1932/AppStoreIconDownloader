import os
import sys

from dotenv import load_dotenv

# for bundled MEI, try to cd the _MEIPASS folder
if hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)

load_dotenv()

api_key = os.getenv('API_KEY')
cse_id = os.getenv('CSE_ID')
