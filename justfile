build-image-kinoite:
	bluebuild generate ./recipes/kinoite.yml -o Containerfile
	bluebuild build ./recipes/kinoite.yml

build-image-kinoite-nvidia:
	bluebuild generate ./recipes/kinoite-nvidia.yml -o Containerfile
	bluebuild build ./recipes/kinoite-nvidia.yml

build-iso-kinoite-from-ghcr-image:
	bluebuild generate-iso --iso-name kinoite.iso image ghcr.io/purkkis/kinoite:daily

build-iso-kinoite-nvidia-from-ghcr-image:
	bluebuild generate-iso --iso-name kinoite-nvidia.iso image ghcr.io/purkkis/kinoite-nvidia:daily

build-iso-kinoite-nvidia-from-recipe:
	bluebuild generate-iso --iso-name kinoite-nvidia.iso recipe recipes/kinoite-nvidia.yml
