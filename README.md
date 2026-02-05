## MVP Telegram parser (Telethon) → POST to your API.

Что упрощено/убрано:

- нет интерактивной консоли
- нет periodic stats/мониторинга
- нет "угадывания" группы по тексту (группа определяется строго по каналу)
- нет лишних полей/логики силы сигнала вне парсеров
- нет отдельного "parser" для extract_price (только helper)
- один aiohttp.ClientSession на всё время работы
- в payload добавлены chat_id + message_id (для дедупа в БД)

Ожидает config json (по умолчанию watchdog_config.json) <- посмотри его 

// группа для теста - bitcoin

# Как запускать:

запускаешь сайт командой из главной директории

```
uvicorn api:app --reload --port 8000
```

и все

# todo

