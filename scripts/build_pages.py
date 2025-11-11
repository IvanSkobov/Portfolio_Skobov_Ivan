import shutil
import pathlib
import sys
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"

def normalize_static_path(p: str) -> str:
	if isinstance(p, str) and p.startswith("/static/"):
		return p.lstrip("/")
	return p


def read_json(path: pathlib.Path, default):
	try:
		with path.open("r", encoding="utf-8") as f:
			return json.load(f)
	except Exception:
		return default


def stub_fastapi_and_import_main():
	# Allow importing main.py without FastAPI at build time
	try:
		if str(BASE_DIR) not in sys.path:
			sys.path.insert(0, str(BASE_DIR))
		from main import get_profile_data, fetch_github_repos  # type: ignore
		return get_profile_data, fetch_github_repos
	except Exception:
		import types
		if "main" in sys.modules:
			del sys.modules["main"]
		if str(BASE_DIR) not in sys.path:
			sys.path.insert(0, str(BASE_DIR))
		fastapi_stub = types.ModuleType("fastapi")
		responses_stub = types.ModuleType("fastapi.responses")
		staticfiles_stub = types.ModuleType("fastapi.staticfiles")
		templating_stub = types.ModuleType("fastapi.templating")

		class _Dummy:
			def __init__(self, *args, **kwargs): ...
			def mount(self, *args, **kwargs): ...
			def get(self, *args, **kwargs):
				def _decorator(fn):
					return fn
				return _decorator

		class _EnvDummy:
			def __init__(self, *args, **kwargs): ...

		fastapi_stub.FastAPI = _Dummy
		fastapi_stub.Request = _Dummy
		responses_stub.HTMLResponse = _Dummy
		staticfiles_stub.StaticFiles = _Dummy
		templating_stub.Jinja2Templates = _EnvDummy
		sys.modules["fastapi"] = fastapi_stub
		sys.modules["fastapi.responses"] = responses_stub
		sys.modules["fastapi.staticfiles"] = staticfiles_stub
		sys.modules["fastapi.templating"] = templating_stub
		from main import get_profile_data, fetch_github_repos  # type: ignore
		return get_profile_data, fetch_github_repos


def build_show_repos(profile: dict, fetch_repos_func):
	featured = read_json(DATA_DIR / "featured_repos.json", [])
	repos = fetch_repos_func("IvanSkobov", per_page=100)
	filtered_repos = [r for r in repos if not r.get("archived") and not r.get("disabled")]

	# map from resume
	def get_repo_name_from_url(url: str) -> str:
		if not url:
			return ""
		return url.rstrip("/").split("/")[-1]

	resume_projects_map = {}
	for proj in profile.get("experience_projects", []):
		repo_name = get_repo_name_from_url(proj.get("url", ""))
		if repo_name:
			resume_projects_map[repo_name] = proj

	if featured:
		all_repos_by_name = {r["name"]: r for r in repos if r.get("name")}
		all_repos_by_full = {r["full_name"]: r for r in repos if r.get("full_name")}
		show_repos = []
		used_repos = set()
		for slug in featured:
			if slug in used_repos:
				continue
			repo = all_repos_by_name.get(slug) or all_repos_by_full.get(slug)
			if repo:
				show_repos.append(repo)
				used_repos.add(slug)
			elif slug in resume_projects_map:
				proj = resume_projects_map[slug]
				fallback_repo = {
					"name": slug,
					"full_name": f"IvanSkobov/{slug}",
					"description": proj.get("name", ""),
					"html_url": proj.get("url", ""),
					"language": None,
					"stargazers_count": 0,
					"forks_count": 0,
					"updated_at": None,
					"homepage": None,
					"archived": False,
					"disabled": False,
				}
				stack = proj.get("stack", "").lower()
				if any(x in stack for x in ["python", "django", "flask", "pygame", "telegram"]):
					fallback_repo["language"] = "Python"
				elif any(x in stack for x in ["javascript", "html", "css"]):
					fallback_repo["language"] = "JavaScript"
				show_repos.append(fallback_repo)
				used_repos.add(slug)
	else:
		python_repos = [r for r in filtered_repos if r.get("language") == "Python"]
		other_repos = [r for r in filtered_repos if r not in python_repos]
		show_repos = (python_repos[:6] if len(python_repos) >= 6 else python_repos) + other_repos[: (12 - len(python_repos[:6]))]
	return show_repos


def main():
	get_profile_data, fetch_github_repos = stub_fastapi_and_import_main()
	profile = get_profile_data()
	screenshots = read_json(DATA_DIR / "screenshots.json", {})
	# Normalize leading slashes for GitHub Pages
	screenshots = {k: [normalize_static_path(x) for x in v] for k, v in screenshots.items()}
	if isinstance(profile.get("photo"), str):
		profile["photo"] = normalize_static_path(profile["photo"])
	if isinstance(profile.get("certificates"), list):
		for cert in profile["certificates"]:
			if isinstance(cert, dict) and "image" in cert and isinstance(cert["image"], str):
				cert["image"] = normalize_static_path(cert["image"])

	# Jinja env with url_for stub to static files
	def url_for(name: str, path: str = "") -> str:
		if name == "static":
			p = path.lstrip("/")
			return f"static/{p}"
		return "#"

	env = Environment(
		loader=FileSystemLoader(str(TEMPLATES_DIR)),
		autoescape=select_autoescape(enabled_extensions=("html",))
	)
	env.globals["url_for"] = url_for

	template = env.get_template("index.html")
	repos = build_show_repos(profile, fetch_github_repos)
	html = template.render(profile=profile, repos=repos, screenshots=screenshots)

	DOCS_DIR.mkdir(exist_ok=True)
	# copy static folder
	target_static = DOCS_DIR / "static"
	if target_static.exists():
		shutil.rmtree(target_static)
	shutil.copytree(STATIC_DIR, target_static)

	# write index.html
	(DOCS_DIR / "index.html").write_text(html, encoding="utf-8")
	# prevent Jekyll from processing
	(DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")
	print("Built docs/index.html and copied static/")


if __name__ == "__main__":
	main()


