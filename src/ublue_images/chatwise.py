import requests
from pydantic import BaseModel
from yaml import safe_load


class File(BaseModel):
    url: str


class ChatWiseLatestYAML(BaseModel):
    version: str
    files: list[File]


class ChatWiseReleaseItem(BaseModel):
    latest_yaml_url: str


def get_rpm_download_url(release: ChatWiseReleaseItem):
    response = requests.get(release.latest_yaml_url)
    response.raise_for_status()
    latest = ChatWiseLatestYAML.model_validate(safe_load(response.text))
    base: str = "https://releases.chatwise.app"
    for file in latest.files:
        if file.url.endswith(".rpm"):
            return f"{base}/{file.url}"
    raise ValueError("No .rpm file found in the Chatwise Release")


if __name__ == "__main__":
    latest_yaml = """# https://releases.chatwise.app/latest-linux.yml
version: 26.8.0
files:
  - url: ChatWise-26.8.0.AppImage
    sha512: I2Lvy3D2buZc45c86acAbu1gzZraJxqoT2+zL9AvB1bg8JXWsQd5kPDVoq35ng4hXsQbimCy/xfKc0wjLbx7pg==
    size: 128582495
    blockMapSize: 136051
  - url: ChatWise-26.8.0.deb
    sha512: phCuHkUNGKksJOx52lfrmy6w3MfFTsZdPlL4Iz2gctfVJhhyAfgX4rVC8f2GQYwWk8OqxgiC4LssYXJAwJyxmg==
    size: 100056968
  - url: ChatWise-26.8.0.deb
    sha512: phCuHkUNGKksJOx52lfrmy6w3MfFTsZdPlL4Iz2gctfVJhhyAfgX4rVC8f2GQYwWk8OqxgiC4LssYXJAwJyxmg==
    size: 100056968
  - url: ChatWise-26.8.0.rpm
    sha512: FT6FHsLPVzYRr+oq4EZVwvcssYbbZB6IYuz+QhJGw+DLcEzk72j/pnB/i/jUwvgtsICLLfx6H5QIpvelezY8OQ==
    size: 87472641
  - url: ChatWise-26.8.0.rpm
    sha512: FT6FHsLPVzYRr+oq4EZVwvcssYbbZB6IYuz+QhJGw+DLcEzk72j/pnB/i/jUwvgtsICLLfx6H5QIpvelezY8OQ==
    size: 87472641
path: ChatWise-26.8.0.AppImage
sha512: I2Lvy3D2buZc45c86acAbu1gzZraJxqoT2+zL9AvB1bg8JXWsQd5kPDVoq35ng4hXsQbimCy/xfKc0wjLbx7pg==
releaseNotes: |
  - add gemini 3.7 flash, grok 4.6
releaseDate: '2026-08-13T23:29:26.917Z'
"""
    json_as_yaml = safe_load(latest_yaml)
    latest = ChatWiseLatestYAML.model_validate(json_as_yaml)
    print(latest)

    chatwise = ChatWiseReleaseItem(latest_yaml_url="https://releases.chatwise.app/latest-linux.yml")
    print(get_rpm_download_url(chatwise))
