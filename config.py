import os

from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env файла

BOT_TOKEN = os.getenv('BOT_TOKEN')

GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
GOOGLE_SHEETS_NAME = os.getenv('GOOGLE_SHEETS_NAME')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
