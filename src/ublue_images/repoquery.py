import subprocess as sp
import json


def latest_installed_versions(packages: list[str]):
    versions = {}
    for package in packages:
        qf = '{"%{name}": "%{version}"}\n'
        cmd = f"dnf repoquery --installed --qf '{qf}' {package}"
        result = sp.run(cmd, shell=True, capture_output=True, text=True)
        if not result.stdout.strip():
            versions[package] = None
        else:
            versions[package] = json.loads(result.stdout.strip())[package]
    return versions


if __name__ == "__main__":
    x = latest_installed_versions(["git", "cursor", "wget", "curl"])
    print(json.dumps(x, indent=2))
