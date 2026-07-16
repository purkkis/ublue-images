"""
modules:
  - type: dnf
    install:
      packages:
        - direct_downloads/protonmail-bridge.rpm
        - direct_downloads/chatwise.rpm
        - direct_downloads/positron.rpm
        - github_releases/dbeaver.rpm
        - github_releases/opencode.rpm
        - github_releases/dbvr.rpm
"""

from typing import Literal

import yaml
from pydantic import BaseModel


class Module(BaseModel):
    type: Literal["dnf"] = "dnf"
    install: dict[str, list[str]]


class Modules(BaseModel):
    modules: list[Module]


if __name__ == "__main__":
    modules = Modules(
        modules=[
            Module(
                type="dnf",
                install={
                    "packages": [
                        "direct_downloads/protonmail-bridge.rpm",
                        "direct_downloads/chatwise.rpm",
                        "direct_downloads/positron.rpm",
                        "github_releases/dbeaver.rpm",
                        "github_releases/opencode.rpm",
                        "github_releases/dbvr.rpm",
                    ]
                },
            )
        ]
    )
    print(yaml.dump(modules.model_dump(), indent=2))
