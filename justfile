build-image-kinoite:
	bluebuild generate ./recipes/kinoite.yml -o Containerfile
	bluebuild build ./recipes/kinoite.yml

build-image-kinoite-nvidia:
	bluebuild generate ./recipes/kinoite-nvidia.yml -o Containerfile
	bluebuild build ./recipes/kinoite-nvidia.yml

build-iso-kinoite-from-ghcr-image:
	bluebuild generate-iso --iso-name kinoite.iso -B docker image ghcr.io/purkkis/kinoite:daily

build-iso-kinoite-nvidia-from-ghcr-image:
	bluebuild generate-iso --iso-name kinoite-nvidia.iso -B docker image ghcr.io/purkkis/kinoite-nvidia:daily

github-release-download:
	wget -O /tmp/github.json https://api.github.com/repos/sst/opencode/releases/latest
	uv run datamodel-codegen \
		--input /tmp/github.json \
		--input-file-type json \
		--output src/ublue_images/models/github.py \
		--class-name GithubReleases

update-github-release-tags:
	uv run src/ublue_images/tags.py --refresh
