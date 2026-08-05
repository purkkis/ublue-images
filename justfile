build-image-kinoite:
	bluebuild generate ./recipes/kinoite.yml -o Containerfile
	bluebuild build ./recipes/kinoite.yml

build-image-kinoite-nvidia:
	bluebuild generate ./recipes/kinoite-nvidia.yml -o Containerfile
	bluebuild build ./recipes/kinoite-nvidia.yml

build-image-silverblue:
	bluebuild generate ./recipes/silverblue.yml -o Containerfile
	bluebuild build ./recipes/silverblue.yml

build-image-silverblue-nvidia:
	bluebuild generate ./recipes/silverblue-nvidia.yml -o Containerfile
	bluebuild build ./recipes/silverblue-nvidia.yml

build-iso-kinoite-from-ghcr-image:
	bluebuild generate-iso --iso-name kinoite.iso image ghcr.io/purkkis/kinoite:latest

build-iso-kinoite-nvidia-from-ghcr-image:
	bluebuild generate-iso --iso-name kinoite-nvidia.iso image ghcr.io/purkkis/kinoite-nvidia:latest

build-iso-silverblue-from-ghcr-image:
	bluebuild generate-iso --iso-name silverblue.iso image ghcr.io/purkkis/silverblue:latest

build-iso-silverblue-nvidia-from-ghcr-image:
	bluebuild generate-iso --iso-name silverblue-nvidia.iso image ghcr.io/purkkis/silverblue-nvidia:latest

github-release-download:
	wget -O /tmp/github.json https://api.github.com/repos/dbeaver/dbeaver/releases/latest
	uv run datamodel-codegen \
		--input /tmp/github.json \
		--input-file-type json \
		--output src/ublue_images/models/github_raw.py \
		--class-name GithubReleases

update-github-releases:
	uv run ublue-images github-releases refresh
