import argparse
import base64
import glob
import io
import json
import os
import sys
import urllib.error
import urllib.request

import textlayer
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


def find_empty_slides(slides):
    empty = []
    for slide in slides:
        prompt = (slide.get("prompt") or "").strip()
        if not prompt:
            empty.append(slide.get("id", "?"))
    return empty


def compose_prompt(job, slide):
    slide_prompt = slide["prompt"]
    if job.get("mode") == "raw":
        return slide_prompt
    parts = []
    style = (job.get("style") or "").strip()
    if style:
        parts.append("Overall visual style: " + style + ".")
    master = (job.get("master") or "").strip()
    if master:
        parts.append(master)
    parts.append(slide_prompt)
    text = "\n\n".join(parts)
    if job.get("text_mode") == "overlay":
        caption = slide.get("caption") or {}
        position = caption.get("position", "top-left")
        text += (
            "\n\nLeave the "
            + position
            + " area clean and open with no text or lettering rendered in the image; "
            + "a caption will be placed there separately."
        )
    return text


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


def call_image_api(key, model, prompt, size, quality, count):
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": count,
        }
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
    with urllib.request.urlopen(request, timeout=600) as response:
        body = json.loads(response.read().decode("utf-8"))
    return [item["b64_json"] for item in body["data"]]


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


def print_estimate(job, slides, variants, per_cost, only):
    images = len(slides) * variants
    print("Job:      " + job.get("name", "untitled"))
    print("Mode:     " + job.get("mode", "branded"))
    style = (job.get("style") or "").strip()
    if style:
        print("Style:    " + style)
    if job.get("text_mode") == "overlay":
        print("Text:     overlay (exact captions composited on top)")
    print(
        "Format:   " + job.get("format", "?") + "  (" + job.get("size", "?") + ")"
    )
    print("Quality:  " + job.get("quality", "?"))
    if only:
        print("Reshoot:  " + ", ".join(slide["id"] for slide in slides))
    print("Variants: " + str(variants) + " per slide")
    print("Images:   " + str(images))
    print("")
    for slide in slides:
        print("  " + slide["id"] + "   $" + format(per_cost * variants, ".3f"))
    print("")
    print("Estimated total: $" + format(per_cost * images, ".3f"))
    print("")


def resolve_job(workspace_path, selector):
    if selector:
        target = workspace.job_dir(workspace_path, selector)
        if not os.path.isfile(os.path.join(target, "job.json")):
            print(
                "No job with id '" + selector + "' under .postsmith/jobs/",
                file=sys.stderr,
            )
            sys.exit(2)
        return selector, target
    latest = workspace.latest_job(workspace_path)
    if not latest:
        print("No jobs found. Run the wizard or write a job.json first.", file=sys.stderr)
        sys.exit(2)
    return latest, workspace.job_dir(workspace_path, latest)


def select_slides(job, only):
    slides = job["slides"]
    if not only:
        return slides
    wanted = [token.strip() for token in only.split(",") if token.strip()]
    index = {slide["id"]: slide for slide in slides}
    missing = [token for token in wanted if token not in index]
    if missing:
        print("Unknown slide ids: " + ", ".join(missing), file=sys.stderr)
        sys.exit(2)
    return [index[token] for token in wanted]


def clear_slide_files(out_dir, slide_id):
    for path in glob.glob(os.path.join(out_dir, slide_id + "*.png")):
        os.remove(path)


def brand_summary(brand):
    if not isinstance(brand, dict):
        return {}
    return {"palette": brand.get("palette", {}), "fonts": brand.get("fonts", {})}


def write_manifest(out_dir, job, job_id, frames, brand):
    manifest = {
        "id": job_id,
        "name": job["name"],
        "mode": job.get("mode", "branded"),
        "style": job.get("style", ""),
        "text_mode": job.get("text_mode", "baked"),
        "format": job.get("format", ""),
        "size": job.get("size", ""),
        "quality": job.get("quality", ""),
        "model": job.get("model", ""),
        "brand": brand_summary(brand),
        "total_cost": round(sum(frame["cost"] for frame in frames), 4),
        "frames": frames,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    return manifest


def run(selector=None, assume_yes=False, only=None, variants=1):
    workspace_path = workspace.init_workspace()
    config = workspace.load_config(workspace_path)
    brand = workspace.read_json(workspace.resolve_brand_path(workspace_path, config), {})

    job_id, out_dir = resolve_job(workspace_path, selector)
    job = load_job(os.path.join(out_dir, "job.json"))
    variants = max(1, int(variants or 1))

    slides = select_slides(job, only)
    empty = find_empty_slides(slides)
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
    per_cost = per_image_cost(quality, size)

    print_estimate(job, slides, variants, per_cost, only)

    if not confirm("Read OPENAI_API_KEY from .env to start this run?", assume_yes):
        print("Stopped before reading the key. Nothing was spent.")
        return
    key = load_api_key(workspace.project_root(workspace_path))

    if not confirm("Spend the estimate above on gpt-image-2?", assume_yes):
        print("Stopped before generating. Nothing was spent.")
        return

    with open(os.path.join(out_dir, "master.txt"), "w", encoding="utf-8") as handle:
        handle.write(job.get("master") or "")

    overlay = job.get("text_mode") == "overlay"
    bake = overlay and textlayer.available()
    if overlay and not bake:
        print(
            "Pillow not installed: captions are composited in the gallery instead of "
            "baked into the PNG. Install Pillow to bake exact text into saved files."
        )

    new_frames = []
    for slide in slides:
        slide_id = slide["id"]
        caption = slide.get("caption") if overlay else None
        prompt = compose_prompt(job, slide)
        if only:
            clear_slide_files(out_dir, slide_id)
        print("Generating " + slide_id + " (" + str(variants) + ") ...")
        try:
            images = call_image_api(key, model, prompt, size, quality, variants)
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

        for index, b64 in enumerate(images, 1):
            png_bytes = crop_to_format(base64.b64decode(b64), fmt)
            suffix = "" if index == 1 else "-" + str(index)
            file_name = slide_id + suffix + ".png"
            text_baked = False
            if caption and bake:
                with open(os.path.join(out_dir, slide_id + suffix + ".raw.png"), "wb") as handle:
                    handle.write(png_bytes)
                png_bytes = textlayer.apply(png_bytes, caption, brand, workspace.fonts_dir(workspace_path))
                text_baked = True
            with open(os.path.join(out_dir, file_name), "wb") as handle:
                handle.write(png_bytes)
            frame = {
                "id": slide_id,
                "variant": index,
                "file": file_name,
                "prompt": prompt,
                "cost": per_cost,
            }
            if caption:
                frame["caption"] = caption
                frame["text_baked"] = text_baked
            new_frames.append(frame)

    existing = workspace.read_json(os.path.join(out_dir, "manifest.json"), None)
    if only and isinstance(existing, dict) and existing.get("frames"):
        reshot = {slide["id"] for slide in slides}
        kept = [frame for frame in existing["frames"] if frame.get("id") not in reshot]
        frames = kept + new_frames
    else:
        frames = new_frames
    frames.sort(key=lambda frame: (frame.get("id", ""), frame.get("variant", 1)))

    manifest = write_manifest(out_dir, job, job_id, frames, brand)

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
            "style": job.get("style", ""),
            "text_mode": job.get("text_mode", "baked"),
            "model": model,
            "frames": len(frames),
            "cost": manifest["total_cost"],
            "thumb": frames[0]["file"] if frames else "",
        },
    )

    print("")
    print("Saved " + str(len(new_frames)) + " images to " + out_dir)
    print("Next: serve the gallery to review them.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate images for a postsmith job.")
    parser.add_argument("--job", help="job id under .postsmith/jobs/ (default: latest)")
    parser.add_argument("--only", help="comma-separated slide ids to reshoot")
    parser.add_argument("-n", "--variants", type=int, default=1, help="versions per slide")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="skip both confirmations (key read and spend)",
    )
    args = parser.parse_args(argv)
    run(args.job, assume_yes=args.yes, only=args.only, variants=args.variants)


if __name__ == "__main__":
    main()
