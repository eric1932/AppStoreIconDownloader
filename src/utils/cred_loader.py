import os
import sys

from dotenv import load_dotenv

# for bundled MEI, try to cd the _MEIPASS folder
if hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)

load_dotenv()

API_KEY = os.getenv('API_KEY')
CSE_ID = os.getenv('CSE_ID')
