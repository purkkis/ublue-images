build-kinoite:
	bluebuild generate ./recipes/kinoite.yml -o Containerfile
	bluebuild build ./recipes/kinoite.yml

build-kinoite-nvidia:
	bluebuild generate ./recipes/kinoite-nvidia.yml -o Containerfile
	bluebuild build ./recipes/kinoite-nvidia.yml

kinoite-nvidia-build-iso:
	bluebuild generate-iso --iso-name kinoite-nvidia.iso recipe recipes/kinoite-nvidia.yml

kinoite-nvidia-iso:
	bluebuild generate-iso --iso-name kinoite-nvidia.iso image ghcr.io/purkkis/kinoite-nvidia:daily

kinoite-iso:
	bluebuild generate-iso --iso-name kinoite.iso image ghcr.io/purkkis/kinoite:daily

github-release-download:
	wget -O /tmp/github.json https://api.github.com/repos/sst/opencode/releases/latest
	uv run datamodel-codegen \
		--input /tmp/github.json \
		--input-file-type json \
		--output src/ublue_images/models/github.py
