from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import pathlib
import json

BASE_DIR = pathlib.Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

# Ensure directories exist (useful for first run)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Portfolio - Ivan Skobov", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def load_screenshots_config() -> dict:
	"""Load screenshots mapping from data/screenshots.json if exists."""
	config_path = DATA_DIR / "screenshots.json"
	if not config_path.exists():
		return {}
	try:
		with config_path.open("r", encoding="utf-8") as f:
			return json.load(f)
	except Exception:
		return {}


def load_certificates() -> list[dict]:
	"""Load certificates from data/certificates.json if exists."""
	config_path = DATA_DIR / "certificates.json"
	if not config_path.exists():
		return []
	try:
		with config_path.open("r", encoding="utf-8") as f:
			data = json.load(f)
			if isinstance(data, list):
				return data
	except Exception:
		pass
	return []


def load_featured_repos() -> list[str]:
	"""Load preferred repo names/full_names to display from data/featured_repos.json."""
	config_path = DATA_DIR / "featured_repos.json"
	if not config_path.exists():
		return []
	try:
		with config_path.open("r", encoding="utf-8") as f:
			data = json.load(f)
			if isinstance(data, list):
				return [str(item) for item in data]
	except Exception:
		pass
	return []


def fetch_github_repos(username: str, per_page: int = 100) -> list[dict]:
	"""
	Fetch public repositories for the user from GitHub REST API.
	No auth token used here; rate-limited to 60 req/hour by IP.
	"""
	url = f"https://api.github.com/users/{username}/repos"
	params = {"per_page": per_page, "sort": "updated", "direction": "desc"}
	headers = {
		"Accept": "application/vnd.github+json"
	}
	try:
		resp = requests.get(url, params=params, headers=headers, timeout=15)
		resp.raise_for_status()
		repos = resp.json()
	except Exception:
		return []

	# Map to compact structure
	result = []
	for r in repos:
		result.append({
			"name": r.get("name"),
			"full_name": r.get("full_name"),
			"description": r.get("description"),
			"html_url": r.get("html_url"),
			"language": r.get("language"),
			"stargazers_count": r.get("stargazers_count") or 0,
			"forks_count": r.get("forks_count") or 0,
			"updated_at": r.get("updated_at"),
			"homepage": r.get("homepage"),
			"archived": r.get("archived"),
			"disabled": r.get("disabled"),
		})
	return result


def get_profile_data() -> dict:
	"""
	Static profile data based on provided resume.
	Can be moved to a config later.
	"""
	return {
		"name": "Иван Скобов",
		"title": "Python Developer (Junior)",
		"location": "Самара, Готов к удалёнке",
		"photo": "/static/images/profile/photo.jpg",
		"contacts": {
			"email": "5secondvano@gmail.com",
			"phone_primary": "+7 917 155 57 70",
			"phone_secondary": "+7 705 142 95 55",
			"telegram": "https://t.me/i5second",
			"github": "https://github.com/IvanSkobov"
		},
		"skills": [
			"Python (3.x), ООП",
			"Flask / Django / FastAPI",
			"SQLite, PostgreSQL, SQLAlchemy",
			"Телеграм-боты (aiogram, telebot)",
			"Git / GitHub / Docker (базовый)",
			"HTML, CSS, Bootstrap (базовый frontend)"
		],
		"experience_projects": [
			{
				"name": "FINCONTROL — сервис учёта личных финансов",
				"url": "https://github.com/IvanSkobov/Fincontrol",
				"stack": "Django, aiogram",
				"summary": "Доходы/расходы, категории, бюджеты, аналитика, экспорт, уведомления; веб + Telegram-бот."
			},
			{
				"name": "Приложения для расчёта зарплаты",
				"url": "https://github.com/IvanSkobov/Work_Calc_time",
				"stack": "JavaScript, CSS, HTML, Batchfile",
				"summary": "Поддержка команд/inline-кнопок, хранение и статистика расчётов, экспорт в Excel."
			},
			{
				"name": "Веб-сайт на Flask с базой данных",
				"url": "https://github.com/IvanSkobov/WebDG_Project",
				"stack": "Flask, SQLite, Bootstrap, FullCalendar",
				"summary": "Категории и карточки ссылок, добавление/редактирование через веб."
			},
			{
				"name": "2D-игра (Pygame)",
				"url": "https://github.com/IvanSkobov/2D-platform",
				"stack": "Pygame",
				"summary": "Уровни, коллизии, победа/поражение; структура: player.py, level.py, game.py, main.py."
			},
			{
				"name": "Парсер вакансий",
				"url": "https://github.com/IvanSkobov/job-parser-system",
				"stack": "Requests, BeautifulSoup, SQLite, CSV",
				"summary": "Парсинг вакансий, сохранение в SQLite, экспорт в CSV."
			},
			{
				"name": "Телеграм-бот Lineage-2 справка",
				"url": "https://github.com/IvanSkobov/telegram_ai_bot",
				"stack": "python-telegram-bot 20.7, SQLite",
				"summary": "Кэширование результатов, логирование, хранение данных в SQLite."
			}
		],
		"education": [
			"Курсы: Python-разработчик (ZeroCoder)",
			"Университет «Синергия» (Fullstack-разработчик) — в процессе",
			"Среднее профессиональное образование (колледж)"
		],
		"certificates": load_certificates(),
	}


def get_repo_name_from_url(url: str) -> str:
	"""Extract repository name from GitHub URL."""
	if not url:
		return ""
	parts = url.rstrip("/").split("/")
	return parts[-1] if parts else ""


def enrich_repos_with_resume_data(repos: list[dict], profile: dict) -> list[dict]:
	"""
	Enrich repository data with project names from resume experience_projects.
	Uses project name (not summary) as description for display.
	"""
	# Create mapping: repo_name -> {name, stack, summary}
	resume_map = {}
	for proj in profile.get("experience_projects", []):
		repo_name = get_repo_name_from_url(proj.get("url", ""))
		if repo_name:
			resume_map[repo_name] = {
				"name": proj.get("name", ""),
				"stack": proj.get("stack", ""),
				"summary": proj.get("summary", "")
			}
	
	# Enrich repos with resume data
	for repo in repos:
		repo_name = repo.get("name", "")
		if repo_name in resume_map:
			# Use project name from resume as description (not summary)
			repo["description"] = resume_map[repo_name]["name"]
			# Store stack and summary for potential future use
			repo["resume_stack"] = resume_map[repo_name]["stack"]
			repo["resume_summary"] = resume_map[repo_name]["summary"]
	
	return repos


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
	profile = get_profile_data()
	repos = fetch_github_repos("IvanSkobov", per_page=100)
	# предпочтительно показать отобранные проекты
	featured_slugs = load_featured_repos()
	filtered_repos = [
		r for r in repos if not r.get("archived") and not r.get("disabled")
	]
	
	# Create mapping from resume projects
	resume_projects_map = {}
	for proj in profile.get("experience_projects", []):
		repo_name = get_repo_name_from_url(proj.get("url", ""))
		if repo_name:
			resume_projects_map[repo_name] = proj
	
	if featured_slugs:
		# Check all repos including archived for featured repos
		all_repos_by_name = {r["name"]: r for r in repos if r.get("name")}
		all_repos_by_full = {r["full_name"]: r for r in repos if r.get("full_name")}
		show_repos = []
		used_repos = set()  # Track repos already added to avoid duplicates
		
		for slug in featured_slugs:
			# Skip if already added
			if slug in used_repos:
				continue
				
			# First try to find in all repos (including archived)
			repo = all_repos_by_name.get(slug) or all_repos_by_full.get(slug)
			if repo:
				show_repos.append(repo)
				used_repos.add(slug)
			elif slug in resume_projects_map:
				# Create a fallback repo card from resume data if GitHub repo not found
				proj = resume_projects_map[slug]
				fallback_repo = {
					"name": slug,
					"full_name": f"IvanSkobov/{slug}",
					"description": proj.get("name", ""),
					"html_url": proj.get("url", ""),
					"language": None,  # Will be inferred from stack or left empty
					"stargazers_count": 0,
					"forks_count": 0,
					"updated_at": None,
					"homepage": None,
					"archived": False,
					"disabled": False,
				}
				# Try to infer language from stack
				stack = proj.get("stack", "").lower()
				if "python" in stack or "django" in stack or "flask" in stack or "pygame" in stack or "telegram" in stack:
					fallback_repo["language"] = "Python"
				elif "javascript" in stack or "html" in stack or "css" in stack:
					fallback_repo["language"] = "JavaScript"
				show_repos.append(fallback_repo)
				used_repos.add(slug)
	else:
		python_repos = [r for r in filtered_repos if r.get("language") == "Python"]
		other_repos = [r for r in filtered_repos if r not in python_repos]
		show_repos = (
			python_repos[:6] if len(python_repos) >= 6 else python_repos
		) + other_repos[: (12 - len(python_repos[:6]))]

	# Enrich repos with descriptions from resume
	show_repos = enrich_repos_with_resume_data(show_repos, profile)

	screenshots = load_screenshots_config()
	return templates.TemplateResponse(
		"index.html",
		{
			"request": request,
			"profile": profile,
			"repos": show_repos,
			"screenshots": screenshots
		}
	)


@app.get("/health")
def health():
	return {"status": "ok"}


if __name__ == "__main__":
	import uvicorn
	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
