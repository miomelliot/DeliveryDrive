import subprocess

def run_cmd(command) -> None:
    print(f"📦 Running: {command}")
    subprocess.run(command, shell=True, check=True)
