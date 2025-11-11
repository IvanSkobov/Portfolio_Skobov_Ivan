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
			result[repo_name] = {
				"name": proj.get("name", repo_name),
				"stack": proj.get("stack", ""),
				"summary": proj.get("summary", ""),
				"url": url,
			}
	return result


def guess_repo_url(repo_slug: str, resume_map: dict, github_user: str = "IvanSkobov") -> str:
	# If explicit URL known from resume map, prefer it
	if repo_slug in resume_map and resume_map[repo_slug].get("url"):
		return resume_map[repo_slug]["url"]
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
		# Fallback minimal profile
		return {
			"name": "Иван Скобов",
			"title": "Python Developer",
			"location": "",
			"photo": "static/images/profile/photo.jpg",
			"contacts": {
				"github": "https://github.com/IvanSkobov"
			},
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

	# Build projects list for template
	projects = []
	for slug in featured:
		title = resume_map.get(slug, {}).get("name", slug)
		summary = resume_map.get(slug, {}).get("summary", "")
		stack = resume_map.get(slug, {}).get("stack", "")
		url = guess_repo_url(slug, resume_map)
		shots = screenshots.get(slug, [])
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


