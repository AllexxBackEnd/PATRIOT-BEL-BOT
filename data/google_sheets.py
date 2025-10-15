import datetime
import logging

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_SHEETS_CREDENTIALS, SPREADSHEET_ID

# Настройки
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = GOOGLE_SHEETS_CREDENTIALS
SPREADSHEET_ID = SPREADSHEET_ID

logger = logging.getLogger("bot_logger")


class GoogleSheetsManager:
    def __init__(self):
        self.client = None
        self.sheet = None
        self.connect()

    def connect(self):
        """Подключение к Google Таблицам."""
        try:
            creds = Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            self.client = gspread.authorize(creds)

            # Используем ID таблицы вместо названия
            self.sheet = self.client.open_by_key(SPREADSHEET_ID).sheet1
            logger.info("✅ Успешное подключение к Google Таблицам")

            # Проверяем и исправляем заголовки при подключении
            self._ensure_headers()

        except gspread.SpreadsheetNotFound:
            logger.error(f"❌ Таблица с ID '{SPREADSHEET_ID}' не найдена")
            logger.error("Проверьте ID таблицы и доступ сервисного аккаунта")
            self.sheet = None
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Google Таблицам: {e}")
            self.sheet = None

    def _ensure_headers(self):
        """Проверка и создание правильных заголовков"""
        if self.sheet is None:
            return

        try:
            # Получаем первую строку
            first_row = self.sheet.row_values(1)

            # Ожидаемые заголовки
            expected_headers = [
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

            # Если первая строка пустая или не совпадает с
            # ожидаемыми заголовками
            if not first_row or first_row != expected_headers:
                logger.info("📝 Создаем правильные заголовки в таблице...")
                self.sheet.clear()  # Очищаем лист
                self.sheet.append_row(expected_headers)  # Добавляем заголовки
                logger.info("✅ Заголовки созданы успешно")
            else:
                logger.info("✅ Заголовки уже настроены правильно")

        except Exception as e:
            logger.error(f"❌ Ошибка настройки заголовков: {e}")

    def _get_clean_records(self):
        """Получение записей с обработкой дублирующихся заголовков"""
        try:
            # Используем явное указание заголовков
            expected_headers = [
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

            # Получаем все данные начиная со второй строки
            all_data = self.sheet.get_all_values()

            # Если есть только заголовки или таблица пустая
            if len(all_data) <= 1:
                return []

            # Берем данные начиная со второй строки (после заголовков)
            data_rows = all_data[1:]

            # Преобразуем в словари с правильными заголовками
            records = []
            for row in data_rows:
                if any(row):  # Пропускаем полностью пустые строки
                    # Создаем запись, дополняя пустыми значениями если нужно
                    record = {}
                    for i, header in enumerate(expected_headers):
                        if i < len(row):
                            record[header] = row[i]
                        else:
                            record[header] = ""
                    records.append(record)

            return records

        except Exception as e:
            logger.error(f"❌ Ошибка получения записей: {e}")
            return []

    def save_competitive_result(self, user_data):
        """Сохранение результата в таблицу"""
        if self.sheet is None:
            logger.warning("⚠️ Таблица не доступна - данные не сохранены")
            return False

        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Получаем следующий ID
            records = self._get_clean_records()
            next_id = len(records) + 1

            # Рассчет процента и оценки
            correct_answers = user_data["correct_answers"]
            total_questions = user_data["total_questions"]
            percentage = round((correct_answers / total_questions) * 100, 2)
            grade = self.calculate_grade(percentage)

            row_data = [
                next_id,
                timestamp,
                str(user_data["chat_id"]),
                user_data.get("first_name", ""),
                user_data.get("last_name", ""),
                user_data.get("educational_institution", "Не указано"),
                correct_answers,
                total_questions,
                f"{percentage}%",
                grade,
            ]

            # Добавляем строку в конец таблицы
            self.sheet.append_row(row_data)
            logger.info(
                "✅ Результат сохранен в Google Таблицы для пользователя"
                f"{user_data['chat_id']}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в Google Таблицы: {e}")
            return False

    def calculate_grade(self, percentage):
        """Рассчет оценки на основе процента правильных ответов"""
        if percentage >= 90:
            return "Отлично"
        elif percentage >= 75:
            return "Хорошо"
        elif percentage >= 60:
            return "Удовлетворительно"
        else:
            return "Неудовлетворительно"

    def is_competitive_completed(self, chat_id):
        """Проверка, проходил ли пользователь соревновательный режим"""
        if self.sheet is None:
            return False

        try:
            records = self._get_clean_records()
            for record in records:
                if record.get(
                  "Chat ID"
                 ) and str(record["Chat ID"]) == str(chat_id):
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка проверки завершения режима: {e}")
            return False

    def get_all_results(self):
        """Получение всех результатов из таблицы"""
        return self._get_clean_records()

    def get_statistics(self):
        """Получение статистики по результатам"""
        try:
            results = self.get_all_results()
            if not results:
                return {
                    "total_participants": 0,
                    "average_score": 0,
                    "average_percentage": 0,
                    "best_score": 0,
                }

            total_participants = len(results)
            total_correct = 0
            best_score = 0

            for result in results:
                try:
                    correct = int(result.get("Correct Answers", 0))
                    total_correct += correct
                    if correct > best_score:
                        best_score = correct
                except (ValueError, TypeError):
                    continue

            average_score = (
                round(total_correct / total_participants, 2)
                if total_participants > 0
                else 0
            )

            return {
                "total_participants": total_participants,
                "average_score": average_score,
                "best_score": best_score,
            }
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {"total_participants": 0, "average_score": 0,
                    "best_score": 0}


# Глобальный экземпляр
sheets_manager = GoogleSheetsManager()
