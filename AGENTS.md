# Kinoite BlueBuild image

This project builds custom Fedora Atomic desktop images using [BlueBuild](https://blue-build.org/) recipes.

## Docs

Always check BlueBuild docs from Context7:

- `websites/blue-build`
- `blue-build/website`

Also use web search tools to search online for relevant documentation and examples.

## Repository Structure

- `files/`: Configuration files, RPMs, and scripts to be included in the image.
  - `dnf/`: Repository files and specific RPMs for DNF.
  - `dropbox/`: Build files for Dropbox/Nautilus integration.
  - `scripts/`: Custom scripts for image customization.
  - `usr_lib_sysusers_d/`: System user configuration files.
- `recipes/`: BlueBuild recipe files defining the image composition.
  - `kinoite.yml`: The main recipe for the Kinoite image.
  - `kinoite-nvidia.yml`: Recipe with NVIDIA driver support.
- `src/`: Python source code for helper scripts (e.g., managing RPMs and tags).
- `justfile`: Just runner commands for building and managing the project.
- `pyproject.toml`: Python project configuration.
- `README.md`: Project documentation.
