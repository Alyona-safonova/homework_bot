import logging
import os
import sys
import time

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

logging.basicConfig(
    format="%(asctime)s, %(levelname)s, %(filename)s, %(lineno)s, %(message)s",
    level=logging.DEBUG,
    filename='main.log',
    filemode='w'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(filename)s, %(lineno)s, %(message)s'
)

handler.setFormatter(formatter)


def send_message(bot, message):
    """отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(
            TELEGRAM_CHAT_ID,
            message
        )
    except Exception as error:
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
    api_answer = requests.get(ENDPOINT, headers=HEADERS, params=params)
    status_code = api_answer.status_code
    if status_code == 200:
        homework = api_answer.json()
        return homework
    else:
        if status_code == 503:
            message = f'Недоступность эндпоинта "{ENDPOINT}".'
        else:
            message = 'любые другие сбои'
        raise ConnectionError(message)


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
        raise TypeError('Проверка типа дз')
    return homework


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус."""
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')
    if 'status' not in homework:
        raise Exception('Отсутствует ключ "status" в ответе API')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise Exception(f'Неизвестный статус работы: {homework_status}')

    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in tokens:
        if token is None:
            return False
    return True


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
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(message, bot)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
