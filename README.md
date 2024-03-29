# Homework_bot

## Описание
Telegram-бот, отслеживающий статус домашнего задания, отправленного на проверку в Яндекс.Практикум. Каждые 10 минут отправляет запрос статуса домашнего задания к API Практикум.Домашка. В случае изменения статуса направляет пользователю оповещение в telegram.
Предусмотрено логирование ошибок.

### Как запустить проект:

В первую очередь необходимо зарегистрировать Телеграмм-бота и получить от него токен, узнать свой id в Телеграмме и получить токен API Яндекс.Практикума.

Затем клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/AlexStr94/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
. venv/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Записать три переменных  в общее пространство переменных окружения:

```
export PRACTICUM_TOKEN=<Ваш токен Яндекс.Практикума>
```

```
export TELEGRAM_TOKEN=<Токен телеграмм-бота>
```

```
export TELEGRAM_CHAT_ID=<ваш id в Телеграмме>
```

Запустить файл homework.py
