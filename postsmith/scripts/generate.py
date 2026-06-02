import argparse
import base64
import io
import json
import os
import sys
import urllib.error
import urllib.request

import workspace


API_URL = "https://api.openai.com/v1/images/generations"

COST_TABLE = {
    "low": (0.006, 0.005),
    "medium": (0.053, 0.041),
    "high": (0.211, 0.165),
}


def per_image_cost(quality, size):
    square, rect = COST_TABLE[quality]
    return square if size == "1024x1024" else rect


def load_job(job_file):
    with open(job_file, "r", encoding="utf-8") as handle:
        return json.load(handle)


def find_empty_slides(job):
    empty = []
    for slide in job.get("slides", []):
        prompt = (slide.get("prompt") or "").strip()
        if not prompt:
            empty.append(slide.get("id", "?"))
    return empty


def compose_prompt(job, slide):
    slide_prompt = slide["prompt"]
    if job.get("mode") == "raw":
        return slide_prompt
    master = (job.get("master") or "").strip()
    if not master:
        return slide_prompt
    return master + "\n\n" + slide_prompt


def parse_env_file(path):
    values = {}
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            values[key.strip()] = value
    return values


def load_api_key(search_root):
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    if not os.environ.get("OPENAI_API_KEY"):
        for base in (os.getcwd(), search_root):
            env_path = os.path.join(base, ".env")
            if os.path.exists(env_path):
                for key, value in parse_env_file(env_path).items():
                    os.environ.setdefault(key, value)
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("add OPENAI_API_KEY to .env", file=sys.stderr)
        sys.exit(1)
    return key


def call_image_api(key, model, prompt, size, quality):
    payload = json.dumps(
        {"model": model, "prompt": prompt, "size": size, "quality": quality}
    ).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["data"][0]["b64_json"]


def center_crop(img, ratio_w, ratio_h):
    width, height = img.size
    target = ratio_w / ratio_h
    current = width / height
    if current > target:
        new_w = round(height * target)
        left = (width - new_w) // 2
        return img.crop((left, 0, left + new_w, height))
    new_h = round(width / target)
    top = (height - new_h) // 2
    return img.crop((0, top, width, top + new_h))


def crop_to_format(png_bytes, fmt):
    if fmt not in ("4:5", "9:16"):
        return png_bytes
    try:
        from PIL import Image
    except ImportError:
        print(
            "Pillow not installed; saved full 1024x1536 without cropping to " + fmt,
            file=sys.stderr,
        )
        return png_bytes
    ratio_w, ratio_h = (4, 5) if fmt == "4:5" else (9, 16)
    img = Image.open(io.BytesIO(png_bytes))
    cropped = center_crop(img, ratio_w, ratio_h)
    out = io.BytesIO()
    cropped.save(out, format="PNG")
    return out.getvalue()


def confirm(question, assume_yes):
    if assume_yes:
        return True
    answer = input(question + " [y/N] ").strip().lower()
    return answer in ("y", "yes")


def print_estimate(job, frames_cost):
    print("Job:      " + job.get("name", "untitled"))
    print("Mode:     " + job.get("mode", "branded"))
    print(
        "Format:   "
        + job.get("format", "?")
        + "  ("
        + job.get("size", "?")
        + ")"
    )
    print("Quality:  " + job.get("quality", "?"))
    print("Frames:   " + str(len(frames_cost)))
    print("")
    for slide_id, cost in frames_cost:
        print("  " + slide_id + "   $" + format(cost, ".3f"))
    total = sum(cost for _, cost in frames_cost)
    print("")
    print("Estimated total: $" + format(total, ".3f"))
    print("")


def resolve_job(workspace_path, selector):
    if selector:
        target = workspace.job_dir(workspace_path, selector)
        if not os.path.isfile(os.path.join(target, "job.json")):
            print("No job with id '" + selector + "' under .postsmith/jobs/", file=sys.stderr)
            sys.exit(2)
        return selector, target
    latest = workspace.latest_job(workspace_path)
    if not latest:
        print("No jobs found. Run the wizard or write a job.json first.", file=sys.stderr)
        sys.exit(2)
    return latest, workspace.job_dir(workspace_path, latest)


def write_manifest(out_dir, job, job_id, frames):
    manifest = {
        "id": job_id,
        "name": job["name"],
        "mode": job.get("mode", "branded"),
        "format": job.get("format", ""),
        "size": job.get("size", ""),
        "quality": job.get("quality", ""),
        "model": job.get("model", ""),
        "total_cost": round(sum(frame["cost"] for frame in frames), 4),
        "frames": frames,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    return manifest


def run(selector=None, assume_yes=False):
    workspace_path = workspace.init_workspace()
    job_id, out_dir = resolve_job(workspace_path, selector)
    job = load_job(os.path.join(out_dir, "job.json"))

    empty = find_empty_slides(job)
    if empty:
        print(
            "Refusing to generate: empty slide prompts for ids " + ", ".join(empty),
            file=sys.stderr,
        )
        sys.exit(2)

    quality = job["quality"]
    size = job["size"]
    fmt = job.get("format", "")
    model = job.get("model", "gpt-image-2-2026-04-21")

    frames_cost = [
        (slide["id"], per_image_cost(quality, size)) for slide in job["slides"]
    ]
    print_estimate(job, frames_cost)

    if not confirm("Read OPENAI_API_KEY from .env to start this run?", assume_yes):
        print("Stopped before reading the key. Nothing was spent.")
        return
    key = load_api_key(workspace.project_root(workspace_path))

    if not confirm("Spend the estimate above on gpt-image-2?", assume_yes):
        print("Stopped before generating. Nothing was spent.")
        return

    with open(os.path.join(out_dir, "master.txt"), "w", encoding="utf-8") as handle:
        handle.write(job.get("master") or "")

    frames = []
    for slide in job["slides"]:
        slide_id = slide["id"]
        prompt = compose_prompt(job, slide)
        print("Generating " + slide_id + " ...")
        try:
            b64 = call_image_api(key, model, prompt, size, quality)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")
            print(
                "API error on slide "
                + slide_id
                + " (HTTP "
                + str(error.code)
                + "): "
                + detail,
                file=sys.stderr,
            )
            sys.exit(1)
        except urllib.error.URLError as error:
            print(
                "Network error on slide " + slide_id + ": " + str(error.reason),
                file=sys.stderr,
            )
            sys.exit(1)
        png_bytes = base64.b64decode(b64)
        png_bytes = crop_to_format(png_bytes, fmt)
        file_name = slide_id + ".png"
        with open(os.path.join(out_dir, file_name), "wb") as handle:
            handle.write(png_bytes)
        frames.append(
            {
                "id": slide_id,
                "file": file_name,
                "prompt": prompt,
                "cost": per_image_cost(quality, size),
            }
        )

    manifest = write_manifest(out_dir, job, job_id, frames)

    workspace.upsert_job(
        workspace_path,
        {
            "id": job_id,
            "name": job["name"],
            "created": workspace.utc_now_iso(),
            "format": fmt,
            "size": size,
            "quality": quality,
            "mode": job.get("mode", "branded"),
            "model": model,
            "frames": len(frames),
            "cost": manifest["total_cost"],
            "thumb": frames[0]["file"] if frames else "",
        },
    )

    print("")
    print("Saved " + str(len(frames)) + " frames to " + out_dir)
    print("Next: serve the gallery to review them.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate images for a postsmith job.")
    parser.add_argument("--job", help="job id under .postsmith/jobs/ (default: latest)")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="skip both confirmations (key read and spend)",
    )
    args = parser.parse_args(argv)
    run(args.job, assume_yes=args.yes)


if __name__ == "__main__":
    main()
