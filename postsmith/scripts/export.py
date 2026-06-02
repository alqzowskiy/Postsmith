import argparse
import os
import sys
import zipfile

import workspace


def zip_tree(source_dir, zip_path, arc_root):
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, _, files in os.walk(source_dir):
            for name in files:
                full = os.path.join(root, name)
                archive.write(full, os.path.relpath(full, arc_root))
    return zip_path


def export_one(workspace_path, job_id):
    out_dir = workspace.job_dir(workspace_path, job_id)
    if not os.path.isdir(out_dir):
        print("No such job: " + job_id, file=sys.stderr)
        sys.exit(1)
    zip_path = os.path.join(workspace.exports_dir(workspace_path), job_id + ".zip")
    return zip_tree(out_dir, zip_path, workspace.jobs_dir(workspace_path))


def export_all(workspace_path):
    jobs_root = workspace.jobs_dir(workspace_path)
    if not os.path.isdir(jobs_root) or not os.listdir(jobs_root):
        print("No jobs to export.", file=sys.stderr)
        sys.exit(1)
    zip_path = os.path.join(workspace.exports_dir(workspace_path), "all-jobs.zip")
    return zip_tree(jobs_root, zip_path, workspace_path)


def run(job=None, all_jobs=False):
    workspace_path = workspace.init_workspace()
    if all_jobs:
        result = export_all(workspace_path)
    else:
        job_id = job or workspace.latest_job(workspace_path)
        if not job_id:
            print("No jobs to export.", file=sys.stderr)
            sys.exit(1)
        result = export_one(workspace_path, job_id)
    print("Wrote " + result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Zip a postsmith job for handoff.")
    parser.add_argument("--job", help="job id to export (default: latest)")
    parser.add_argument("--all", action="store_true", help="zip the whole jobs tree")
    args = parser.parse_args(argv)
    run(job=args.job, all_jobs=args.all)


if __name__ == "__main__":
    main()
