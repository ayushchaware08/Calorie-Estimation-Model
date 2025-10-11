import os
import sys

try:
    from roboflow import Roboflow
except Exception as e:
    print("Roboflow SDK not installed. Run: pip install roboflow")
    raise

# optional: load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    # dotenv optional; continue if not present
    pass

def get_env(name, required=True, default=None):
    v = os.getenv(name, default)
    if required and not v:
        print(f"ERROR: {name} not set in environment or .env")
        sys.exit(2)
    return v

def main():
    api_key = get_env("ROBOFLOW_API_KEY")
    workspace = get_env("ROBOFLOW_WORKSPACE")
    project_name = get_env("ROBOFLOW_PROJECT")
    version = int(get_env("ROBOFLOW_VERSION", default="1"))
    fmt = get_env("ROBOFLOW_FORMAT", required=False, default="yolov8")

    print("Roboflow download config:")
    print(f"  workspace={workspace}, project={project_name}, version={version}, format={fmt}")

    rf = Roboflow(api_key=api_key)
    try:
        project = rf.workspace(workspace).project(project_name)
        version_obj = project.version(version)
        print("Requesting dataset download...")
        dataset = version_obj.download(fmt)
        print("Download complete.")
        print("Dataset saved to:", getattr(dataset, "location", "unknown"))
    except Exception as e:
        print("Download failed:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()