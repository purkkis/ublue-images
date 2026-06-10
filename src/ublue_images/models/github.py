from pydantic import BaseModel  # , ConfigDict


class ReleaseAsset(BaseModel):
    # model_config = ConfigDict(extra="ignore")
    name: str
    browser_download_url: str


class GithubReleases(BaseModel):
    # model_config = ConfigDict(extra="ignore")
    tag_name: str
    assets: list[ReleaseAsset]
