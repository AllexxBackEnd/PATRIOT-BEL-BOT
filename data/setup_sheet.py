import gspread
from google.oauth2.service_account import Credentials


def setup_spreadsheet():
    """Настройка таблицы с правильными заголовками"""
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SERVICE_ACCOUNT_FILE = 'google_sheets_credentials.json'
    SPREADSHEET_ID = '1LLEAEobY7e3UD1anWrRYKUBhEnXeus3nUH3PSG1iE2I'

    print("🛠️ НАСТРОЙКА GOOGLE ТАБЛИЦЫ")
    print("=" * 50)

    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        client = gspread.authorize(creds)

        # Открываем таблицу
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.sheet1

        print("✅ Таблица найдена")

        # Получаем текущие данные
        current_data = sheet.get_all_values()
        print(f"📊 Текущее количество строк: {len(current_data)}")

        if current_data:
            print("📝 Первая строка (текущие заголовки):")
            print(f"   {current_data[0]}")

        # Спрашиваем подтверждение на очистку
        response = input(
            "\n⚠️  Очистить таблицу и установить правильные заголовки? (y/n): "
        )

        if response.lower() == "y":
            # Очищаем и устанавливаем правильные заголовки
            sheet.clear()

            headers = [
                "ID",
                "Timestamp",
                "Chat ID",
                "First Name",
                "Last Name",
                "Educational Institution",
                "Correct Answers",
                "Total Questions",
                "Percentage",
                "Grade",
            ]

            sheet.append_row(headers)
            print("✅ Таблица очищена и заголовки установлены!")
            print("📋 Новые заголовки:")
            for i, header in enumerate(headers, 1):
                print(f"   {i}. {header}")
        else:
            print("❌ Настройка отменена")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    setup_spreadsheet()
