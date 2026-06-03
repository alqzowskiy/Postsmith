import argparse
import json
import os

import workspace


SIZE_BY_FORMAT = {
    "4:5": "1024x1536",
    "9:16": "1024x1536",
    "1:1": "1024x1024",
    "16:9": "1536x1024",
}

MODE_BY_CHOICE = {
    "auto": "branded",
    "assisted": "branded",
    "raw": "raw",
}


def ask(question, options, default):
    print("")
    print(question)
    for index, option in enumerate(options, 1):
        marker = "   (default)" if option == default else ""
        print("  " + str(index) + ". " + option + marker)
    raw = input("> ").strip()
    if not raw:
        return default
    if raw.isdigit():
        choice = int(raw)
        if 1 <= choice <= len(options):
            return options[choice - 1]
    return raw


def ask_text(question, default):
    suffix = " [" + default + "]" if default else ""
    raw = input("\n" + question + suffix + "\n> ").strip()
    return raw or default


def ask_int(question, default):
    while True:
        raw = ask_text(question, str(default))
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        print("Enter a positive whole number.")


def brand_language(brand_file, fallback):
    if os.path.exists(brand_file):
        try:
            with open(brand_file, "r", encoding="utf-8") as handle:
                return json.load(handle).get("default_language", fallback)
        except (ValueError, OSError):
            return fallback
    return fallback


def run():
    print("postsmith wizard")
    print("Answer with Enter (keep default), a number, or your own text.")

    workspace_path = workspace.init_workspace()
    config = workspace.load_config(workspace_path)
    defaults = config["defaults"]
    brand_file = workspace.resolve_brand_path(workspace_path, config)

    print("")
    print("Workspace: " + workspace_path)
    print("Brand file: " + brand_file)
    print("Edit it (palette, fonts, tone, never-list) before generating.")

    mode_choice = ask("Prompt mode?", ["auto", "raw", "assisted"], "auto")
    fmt = ask("Format?", ["4:5", "9:16", "1:1", "16:9"], defaults.get("format", "4:5"))
    quality = ask("Quality?", ["low", "medium", "high"], defaults.get("quality", "low"))
    style = ask_text(
        "Visual style? (free text, e.g. editorial photo, anime, high-tech futuristic, "
        "35mm film, 3D render, flat illustration)",
        defaults.get("style", "editorial photo"),
    )
    text_choice = ask(
        "Text rendering?  baked = the model letters the captions; "
        "overlay = postsmith composites exact, guaranteed-correct captions on top",
        ["baked", "overlay"],
        defaults.get("text_mode", "baked"),
    )
    language = ask_text(
        "Caption language?", brand_language(brand_file, defaults.get("language", "en"))
    )
    count = ask_int("Number of slides?", 3)
    name = ask_text("Job name?", "postsmith-job")

    text_mode = "overlay" if text_choice == "overlay" else "baked"
    slides = []
    for n in range(1, count + 1):
        slide = {"id": format(n, "02d"), "prompt": ""}
        if text_mode == "overlay":
            slide["caption"] = {"headline": "", "subhead": "", "position": "top-left"}
        slides.append(slide)

    job = {
        "name": name,
        "mode": MODE_BY_CHOICE.get(mode_choice, "branded"),
        "format": fmt,
        "size": SIZE_BY_FORMAT.get(fmt, "1024x1536"),
        "quality": quality,
        "style": style,
        "text_mode": text_mode,
        "language": language,
        "model": "gpt-image-2-2026-04-21",
        "brand_path": config.get("brand_path", ".postsmith/brand.json"),
        "master": "",
        "slides": slides,
    }

    job_id = workspace.make_job_id(workspace_path, name)
    out_dir = workspace.job_dir(workspace_path, job_id)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "job.json"), "w", encoding="utf-8") as handle:
        json.dump(job, handle, indent=2)
    with open(os.path.join(out_dir, "master.txt"), "w", encoding="utf-8") as handle:
        handle.write("")

    print("")
    print("Created job " + job_id)
    print("Folder: " + out_dir)
    print(
        "The master prompt and every slide prompt are still EMPTY. "
        "Fill them (you or Claude) before generating."
    )
    return job_id


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a postsmith job interactively.")
    parser.parse_args(argv)
    run()


if __name__ == "__main__":
    main()
