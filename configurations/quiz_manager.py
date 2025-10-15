import random

from aiogram.fsm.state import State, StatesGroup

import storage


class QuizStates(StatesGroup):
    """Состояния FSM для управления викториной."""

    choosing_mode = State()
    in_practice_quiz = State()
    in_competitive_quiz = State()
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_educational_info = State()


class QuizManager:
    """Класс для управления вопросами и ответами викторины."""

    def __init__(self, questions):
        self.questions = questions

    def get_random_questions(self, count=5):
        """Возвращает список случайных вопросов."""
        return random.sample(self.questions, min(count, len(self.questions)))

    def get_question(self, questions_list, index):
        """Получает вопрос по индексу из списка."""
        if 0 <= index < len(questions_list):
            return questions_list[index]
        return None

    def check_answer(self, question, answer_text):
        """Проверяет правильность ответа на вопрос."""
        if (
            not question
            or "options" not in question
            or "correct_answer" not in question
        ):
            return False

        try:
            return question[
                            "options"].index(answer_text) == question[
                            "correct_answer"]
        except (ValueError, IndexError):
            return False


class HeroQuizStates(StatesGroup):
    choosing_hero_quiz = State()
    in_hero_quiz = State()


class HeroQuizManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HeroQuizManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.quiz_data = {}  # Хранилище для данных викторин по героям
            self._initialized = True

    def get_hero_questions(self, hero_id: int):
        """Получение 5 случайных вопросов для конкретного героя"""
        if hero_id not in storage.HERO_QUESTIONS:
            return []

        question_indices = storage.HERO_QUESTIONS[hero_id]
        questions = [
            storage.quiz_questions[i]
            for i in question_indices
            if i < len(storage.quiz_questions)
        ]

        # Выбираем 5 случайных вопросов из доступных
        if len(questions) <= 5:
            return questions
        return random.sample(questions, 5)

    def get_question(self, questions_list, index):
        if index < len(questions_list):
            return questions_list[index]
        return None

    def check_answer(self, question, answer_text):
        return question[
            "options"].index(answer_text) == question["correct_answer"]
