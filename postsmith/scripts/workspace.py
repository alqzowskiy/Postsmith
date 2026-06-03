import datetime
import json
import os
import re
import shutil


WORKSPACE_NAME = ".postsmith"
CONFIG_VERSION = 1
TEMPLATE_RELATIVE = ("..", "assets", "brand.example.json")


def default_config():
    return {
        "version": CONFIG_VERSION,
        "brand_path": ".postsmith/brand.json",
        "defaults": {
            "format": "4:5",
            "quality": "low",
            "language": "en",
            "style": "editorial photo",
            "text_mode": "baked",
            "port": 4848,
        },
    }


def find_workspace(start=None):
    current = os.path.abspath(start or os.getcwd())
    while True:
        candidate = os.path.join(current, WORKSPACE_NAME)
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def resolve_workspace(create=True, start=None):
    found = find_workspace(start)
    if found:
        return found
    if not create:
        return None
    root = os.path.abspath(start or os.getcwd())
    path = os.path.join(root, WORKSPACE_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def project_root(workspace):
    return os.path.dirname(workspace)


def config_path(workspace):
    return os.path.join(workspace, "config.json")


def registry_path(workspace):
    return os.path.join(workspace, "registry.json")


def brand_path(workspace):
    return os.path.join(workspace, "brand.json")


def jobs_dir(workspace):
    return os.path.join(workspace, "jobs")


def exports_dir(workspace):
    return os.path.join(workspace, "exports")


def fonts_dir(workspace):
    return os.path.join(workspace, "fonts")


def job_dir(workspace, job_id):
    return os.path.join(jobs_dir(workspace), job_id)


def template_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, *TEMPLATE_RELATIVE))


def read_json(path, fallback):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (ValueError, OSError):
            return fallback
    return fallback


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def write_json_if_absent(path, data):
    if not os.path.exists(path):
        write_json(path, data)


def load_config(workspace):
    config = read_json(config_path(workspace), None)
    if not isinstance(config, dict):
        return default_config()
    merged = default_config()
    merged.update(config)
    defaults = merged.get("defaults")
    if not isinstance(defaults, dict):
        defaults = {}
    base_defaults = default_config()["defaults"]
    base_defaults.update(defaults)
    merged["defaults"] = base_defaults
    return merged


def resolve_brand_path(workspace, config):
    rel = config.get("brand_path", ".postsmith/brand.json")
    if os.path.isabs(rel):
        return rel
    return os.path.normpath(os.path.join(project_root(workspace), rel))


def load_registry(workspace):
    registry = read_json(registry_path(workspace), {"jobs": []})
    if not isinstance(registry, dict) or "jobs" not in registry:
        return {"jobs": []}
    return registry


def save_registry(workspace, registry):
    write_json(registry_path(workspace), registry)


def upsert_job(workspace, entry):
    registry = load_registry(workspace)
    jobs = [job for job in registry.get("jobs", []) if job.get("id") != entry.get("id")]
    jobs.append(entry)
    jobs.sort(key=lambda job: job.get("created", ""), reverse=True)
    registry["jobs"] = jobs
    save_registry(workspace, registry)
    return registry


def utc_now_iso():
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def today_stamp():
    return datetime.date.today().isoformat()


def slugify(name):
    text = (name or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "job"


def make_job_id(workspace, name, date_str=None):
    stamp = date_str or today_stamp()
    base = stamp + "-" + slugify(name)
    candidate = base
    counter = 2
    while os.path.exists(job_dir(workspace, candidate)):
        candidate = base + "-" + str(counter)
        counter += 1
    return candidate


def list_jobs(workspace):
    root = jobs_dir(workspace)
    if not os.path.isdir(root):
        return []
    found = []
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if os.path.isfile(os.path.join(path, "job.json")):
            found.append(name)
    found.sort(key=lambda job_id: os.path.getmtime(job_dir(workspace, job_id)), reverse=True)
    return found


def latest_job(workspace):
    jobs = list_jobs(workspace)
    return jobs[0] if jobs else None


def init_workspace(start=None):
    workspace = resolve_workspace(create=True, start=start)
    os.makedirs(jobs_dir(workspace), exist_ok=True)
    os.makedirs(exports_dir(workspace), exist_ok=True)
    os.makedirs(fonts_dir(workspace), exist_ok=True)
    write_json_if_absent(config_path(workspace), default_config())
    write_json_if_absent(registry_path(workspace), {"jobs": []})
    target = brand_path(workspace)
    if not os.path.exists(target):
        shutil.copyfile(template_path(), target)
    return workspace
