from pydantic import BaseModel


class ReleaseAsset(BaseModel):
    name: str
    browser_download_url: str


class GithubReleases(BaseModel):
    tag_name: str
    assets: list[ReleaseAsset]
