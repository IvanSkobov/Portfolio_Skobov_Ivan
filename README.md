# Портфолио — Иван Скобов

Динамический сайт-портфолио на FastAPI с тёмной темой в стиле GitHub. Проекты подгружаются автоматически из GitHub API, есть возможность добавлять скриншоты к проектам.

## Запуск (локально)

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Откройте `http://127.0.0.1:8000/`.

## Структура

- `main.py` — приложение FastAPI, маршруты и интеграция с GitHub API  
- `templates/` — Jinja2 шаблоны (`base.html`, `index.html`)  
- `static/` — стили, JS и медиа (`/css/style.css`, `/js/main.js`, `/images/...`)  
- `static/images/profile/` — папка для личного фото (photo.jpg)  
- `static/images/certificates/` — папка для изображений сертификатов  
- `data/screenshots.json` — карта скриншотов к репозиториям  
- `data/featured_repos.json` — список репозиториев, которые надо отображать на сайте  
- `data/certificates.json` — список сертификатов с описаниями и ссылками  
## Выбор проектов

Сайт может показывать только избранные репозитории. Укажите имена (или `owner/name`) в `data/featured_repos.json`, напр.:

```json
[
  "Work_Calc_time",
  "job-parser-system",
  "pygame-racing-game",
  "TIR-Game",
  "WebDG_Project",
  "KarapetGaranyan/job-parser-system"
]
```

Если файл пустой или отсутствует, сайт подберёт проекты автоматически (Python + активные репозитории).


## Личное фото

Поместите ваше фото в `static/images/profile/photo.jpg` (или измените путь в `main.py` в функции `get_profile_data()`).  
Рекомендуемый формат: JPG или PNG, квадратное изображение 400x400px или больше.

## Сертификаты

Добавьте сертификаты в `data/certificates.json`. Формат:

```json
[
	{
		"name": "Python-разработчик",
		"issuer": "ZeroCoder",
		"date": "2024",
		"url": "https://example.com/certificate",
		"image": "/static/images/certificates/cert1.jpg"
	}
]
```

Поля:
- `name` (обязательно) — название сертификата
- `issuer` (опционально) — организация/платформа
- `date` (опционально) — дата получения
- `url` (опционально) — ссылка на сертификат
- `image` (опционально) — путь к изображению сертификата

Поместите изображения сертификатов в `static/images/certificates/`.

## Скриншоты проектов

Добавьте изображения в `static/images/<repo>/...` и пропишите пути в `data/screenshots.json`, напр.:

```json
{
  "Fincontrol": [
    "/static/images/fincontrol/shot1.png",
    "/static/images/fincontrol/shot2.png"
  ],
  "WebDG_Project": [
    "/static/images/webdg/shot1.png"
  ]
}
```

Ключ — это `name` репозитория из GitHub API (например, `Fincontrol`, `WebDG_Project` и т.д.).

## Развёртывание в Docker

```bash
docker build -t portfolio:latest .
docker run -d --name portfolio -p 8000:8000 portfolio:latest
```

## Настройка

- Данные контактов и основные сведения берутся из функции `get_profile_data()` в `main.py`.  
- Количество и фильтрация репозиториев регулируются в обработчике `/`.  

## Заметки

- Без токена GitHub API даёт лимит 60 запросов/час на IP. Для продакшна можно добавить `GITHUB_TOKEN` и авторизацию к запросам.

