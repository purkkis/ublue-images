build-kinoite:
	bluebuild generate ./recipes/kinoite.yml -o Containerfile
	bluebuild build ./recipes/kinoite.yml

build-kinoite-nvidia:
	bluebuild generate ./recipes/kinoite-nvidia.yml -o Containerfile
	bluebuild build ./recipes/kinoite-nvidia.yml

build-aurora:
	bluebuild generate ./recipes/aurora.yml -o Containerfile
	bluebuild build ./recipes/aurora.yml

build-aurora-nvidia:
	bluebuild generate ./recipes/aurora-nvidia.yml -o Containerfile
	bluebuild build ./recipes/aurora-nvidia.yml

kinoite-nvidia-build-iso:
	bluebuild generate-iso --iso-name kinoite-nvidia.iso recipe recipes/kinoite-nvidia.yml

kinoite-nvidia-iso:
	bluebuild generate-iso --iso-name kinoite-nvidia.iso image ghcr.io/purkkis/kinoite-nvidia:daily

kinoite-iso:
	bluebuild generate-iso --iso-name kinoite.iso image ghcr.io/purkkis/kinoite:daily
