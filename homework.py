import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(
            TELEGRAM_CHAT_ID,
            message
        )
    except telegram.error.TelegramError as error:
        logger.error(f'сбой при отправке сообщения в Telegram: {error}')
    else:
        logger.info(f'Бот отправил сообщение"{message}')


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    """В качестве параметра функция получает временную метку."""
    """В случае успешного запроса должна вернуть ответ API,
    преобразовав его из формата JSON к типам данных Python."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        api_answer = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        message = f'URL-адрес {ENDPOINT} недоступен: {error}.'
        raise ConnectionError(message)
    status_code = api_answer.status_code
    if status_code != HTTPStatus.OK:
        message = f'В URL-адресе {ENDPOINT}: {status_code} - {api_answer.text}'
        raise ConnectionError(message)
    else:
        homework = api_answer.json()
        return homework


def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response) != dict:
        raise TypeError('Ответ API отличен от словаря')
    try:
        homework = response['homeworks']
    except KeyError:
        message = 'Ошибка словаря по ключу homeworks'
        raise KeyError(message)
    if type(homework) != list:
        raise TypeError('Неверный тип данных у элемента homeworks')
    return homework


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус."""
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')
    if 'status' not in homework:
        raise KeyError('Отсутствует ключ "status" в ответе API')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise Exception(f'Неизвестный статус работы: {homework_status}')

    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens:
        logger.critical('Отсутствие обязательных переменных окружения!')
        sys.exit('Отсутствие переменных окружения!')
    previous_message = 'Сообщений пока нет'
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            if response:
                updates = check_response(response)
                if updates:
                    message = parse_status(updates[0])
                    if message != previous_message:
                        send_message(bot, message)
                        previous_message = message
                else:
                    logger.debug("Отсутствие в ответе новых статусов.")
                current_timestamp = int(time.time())
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(message, bot)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)

logging.basicConfig(
    format="%(asctime)s, %(levelname)s, %(filename)s, %(lineno)s, %(message)s",
    level=logging.DEBUG,
    handlers=[handler],
    filename='main.log',
    filemode='w'
)
