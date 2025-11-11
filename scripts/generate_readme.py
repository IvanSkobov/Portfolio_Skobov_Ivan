import json
import pathlib
from jinja2 import Environment, FileSystemLoader, select_autoescape
import datetime
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
SCRIPTS_DIR = BASE_DIR / "scripts"
README_PATH = BASE_DIR / "README.md"


def read_json(path: pathlib.Path, default):
	try:
		if path.exists():
			with path.open("r", encoding="utf-8") as f:
				return json.load(f)
	except Exception:
		pass
	return default


def normalize_image_path(p: str) -> str:
	# Convert "/static/..." to "static/..." for GitHub
	if p.startswith("/static/"):
		return p.lstrip("/")
	return p


def build_resume_map(profile: dict) -> dict:
	"""
	Map repo_name -> {name, stack, summary, url}
	derived from profile['experience_projects'].
	"""
	result = {}
	for proj in profile.get("experience_projects", []):
		url = proj.get("url") or ""
		repo_name = url.rstrip("/").split("/")[-1] if url else ""
		if repo_name:
			result[repo_name.lower()] = {
				"name": proj.get("name", repo_name),
				"stack": proj.get("stack", ""),
				"summary": proj.get("summary", ""),
				"url": url,
			}
	return result


def guess_repo_url(repo_slug: str, resume_map: dict, github_user: str = "IvanSkobov") -> str:
	# If explicit URL known from resume map, prefer it
	key = repo_slug.lower()
	if key in resume_map and resume_map[key].get("url"):
		return resume_map[key]["url"]
	# Fallback to default user namespace
	if "/" in repo_slug:
		return f"https://github.com/{repo_slug}"
	return f"https://github.com/{github_user}/{repo_slug}"


def load_profile() -> dict:
	# Import lazily to avoid FastAPI runtime if not installed in CI
	sys.path.insert(0, str(BASE_DIR))
	try:
		from main import get_profile_data  # type: ignore
		return get_profile_data()
	except Exception:
		# Second attempt: stub FastAPI imports then retry
		try:
			import types
			# Clear possibly half-initialized module
			if "main" in sys.modules:
				del sys.modules["main"]

			fastapi_stub = types.ModuleType("fastapi")
			responses_stub = types.ModuleType("fastapi.responses")
			staticfiles_stub = types.ModuleType("fastapi.staticfiles")
			templating_stub = types.ModuleType("fastapi.templating")

			class _Dummy:  # pragma: no cover
				def __init__(self, *args, **kwargs):
					pass

				def mount(self, *args, **kwargs):
					return None

			class _EnvDummy:  # pragma: no cover
				def __init__(self, *args, **kwargs):
					pass

			fastapi_stub.FastAPI = _Dummy
			fastapi_stub.Request = _Dummy
			responses_stub.HTMLResponse = _Dummy
			staticfiles_stub.StaticFiles = _Dummy
			templating_stub.Jinja2Templates = _EnvDummy

			sys.modules["fastapi"] = fastapi_stub
			sys.modules["fastapi.responses"] = responses_stub
			sys.modules["fastapi.staticfiles"] = staticfiles_stub
			sys.modules["fastapi.templating"] = templating_stub

			from main import get_profile_data  # type: ignore
			return get_profile_data()
		except Exception:
			# Final fallback minimal profile
			return {
				"name": "Иван Скобов",
				"title": "Python Developer (Junior)",
				"location": "Самара, Готов к удалёнке",
				"photo": "static/images/profile/photo.jpg",
				"contacts": {
					"email": "5secondvano@gmail.com",
					"telegram": "https://t.me/i5second",
					"github": "https://github.com/IvanSkobov",
					"phone_primary": "+7 917 155 57 70",
					"phone_secondary": "+7 705 142 95 55",
				},
				"skills": [
					"Python (3.x), ООП",
					"Flask / Django / FastAPI",
					"SQLite, PostgreSQL, SQLAlchemy",
					"Телеграм-боты (aiogram, telebot)",
					"Git / GitHub / Docker (базовый)",
					"HTML, CSS, Bootstrap (базовый frontend)",
				],
				"experience_projects": [],
			}


def generate():
	profile = load_profile()
	featured = read_json(DATA_DIR / "featured_repos.json", [])
	screenshots = read_json(DATA_DIR / "screenshots.json", {})
	certificates = read_json(DATA_DIR / "certificates.json", [])

	# Normalize paths for GitHub
	for key, shots in list(screenshots.items()):
		screenshots[key] = [normalize_image_path(p) for p in shots]
	for cert in certificates:
		if "image" in cert and isinstance(cert["image"], str):
			cert["image"] = normalize_image_path(cert["image"])
	if "photo" in profile and isinstance(profile["photo"], str):
		profile["photo"] = normalize_image_path(profile["photo"])

	resume_map = build_resume_map(profile)

	def get_shots_for_slug(repo_slug: str) -> list[str]:
		# Try exact key
		if repo_slug in screenshots:
			return screenshots[repo_slug]
		# Try case-insensitive lookup
		low = repo_slug.lower()
		for k, v in screenshots.items():
			if k.lower() == low:
				return v
		return []

	# Build projects list for template
	projects = []

	# Prefer data directly from profile.experience_projects to keep names/summary identical сайту
	experience = profile.get("experience_projects", [])

	# If selection is provided, keep its order; otherwise use all
	if featured:
		# Map by slug
		slug_to_proj = {}
		for proj in experience:
			url = (proj.get("url") or "").rstrip("/")
			slug = url.split("/")[-1] if url else ""
			if slug:
				slug_to_proj[slug.lower()] = proj

		for slug in featured:
			key = slug.lower()
			proj = slug_to_proj.get(key)
			if not proj:
				# Fallback to resume_map or bare slug
				title = resume_map.get(key, {}).get("name", slug)
				summary = resume_map.get(key, {}).get("summary", "")
				stack = resume_map.get(key, {}).get("stack", "")
				url = guess_repo_url(slug, resume_map)
			else:
				title = proj.get("name", slug)
				summary = proj.get("summary", "")
				stack = proj.get("stack", "")
				url = proj.get("url") or guess_repo_url(slug, resume_map)
			shots = get_shots_for_slug(slug)
			cover = shots[0] if shots else None
			projects.append({
				"slug": slug,
				"title": title,
				"url": url,
				"summary": summary,
				"stack": stack,
				"cover": cover,
				"screenshots": shots,
			})
	else:
		for proj in experience:
			url = (proj.get("url") or "").rstrip("/")
			slug = url.split("/")[-1] if url else proj.get("name", "")[:30]
			shots = get_shots_for_slug(slug)
			cover = shots[0] if shots else None
			projects.append({
				"slug": slug,
				"title": proj.get("name", slug),
				"url": proj.get("url") or guess_repo_url(slug, resume_map),
				"summary": proj.get("summary", ""),
				"stack": proj.get("stack", ""),
				"cover": cover,
				"screenshots": shots,
			})

	# Certificates simplified for README
	certs = certificates

	env = Environment(
		loader=FileSystemLoader(str(TEMPLATES_DIR)),
		autoescape=select_autoescape(enabled_extensions=("md",))
	)
	template = env.get_template("readme_template.md.j2")
	content = template.render(
		profile=profile,
		projects=projects,
		certificates=certs,
		now=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
	)

	README_PATH.write_text(content, encoding="utf-8")
	print("README.md regenerated.")


if __name__ == "__main__":
	generate()


