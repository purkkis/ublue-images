# `src/ublue_images` review — findings and fix progress

Review date: 2026-06-10

Scope: Python helpers under `src/ublue_images/`, CLI arguments, download/update logic, and CI/recipe integration.

Related files:

| Area | Paths |
| --- | --- |
| Core downloader | `src/ublue_images/github_release_download.py` |
| Tag refresh / download CLI | `src/ublue_images/tags.py` |
| Hardcoded RPM CLI | `src/ublue_images/rpms.py` |
| Config | `src/ublue_images/files.json`, `src/ublue_images/tags.json` |
| GitHub API model | `src/ublue_images/models/github.py` |
| CLI entrypoint | `src/ublue_images/cli.py` |
| CI | `.github/workflows/build.yml` |
| Image consumption | `recipes/_kinoite-dnf.yml` |
| Local commands | `justfile` (`update-github-release-tags`) |

---

## Architecture (current behavior)

```mermaid
flowchart LR
  tags_json[tags.json]
  files_json[files.json]
  tags_py[tags.py]
  rpms_py[rpms.py]
  cli_py[cli.py / Typer app]
  ghd[GitHubReleaseDownloader]
  gh_api[GitHub API /releases/latest]
  urls[Direct HTTP URLs]
  out_tags[files/dnf/tags]
  out_rpms[files/dnf/rpms]

  cli_py -->|tags refresh| tags_py
  cli_py -->|tags download| tags_py
  cli_py -->|rpms download| rpms_py
  tags_py -->|refresh| gh_api
  tags_py --> tags_json
  tags_py -->|download| ghd
  rpms_py --> ghd
  files_json --> ghd
  tags_json --> ghd
  ghd --> urls
  ghd --> out_tags
  ghd --> out_rpms
```

- **`ublue-images tags refresh`**: For each item in `tags.json` with `repo`, fetches latest release tag and RPM URL from GitHub; rewrites `tags.json`.
- **`ublue-images tags download`**: Reads `tags.json`, downloads enabled items to `files/dnf/tags`.
- **`ublue-images rpms download`**: Reads `files.json`, downloads enabled items to `files/dnf/rpms`.
- **CI** (`.github/workflows/build.yml`): Friday job refreshes `tags.json`; build job caches RPM dirs by config hash and runs download scripts on cache miss.

---

## Findings

Status legend: `[ ]` open · `[~]` in progress · `[x]` fixed · `[-]` wontfix / deferred

### F1 — GitHub release Pydantic model stricter than API (High)

- [x] **Status**
- **Severity:** High
- **Symptom:** `tags.py --refresh` can fail during `GithubReleases.model_validate()` even when the GitHub API returns a valid release.
- **Location:** `src/ublue_images/models/github.py`, used from `get_latest_release()` in `github_release_download.py`.
- **Cause:** Model generated from a single sample (`datamodel-codegen` / `justfile` `github-release-download`) treats many fields as required non-null strings. GitHub’s documented release/asset schema allows nulls (e.g. `name`, `body`, `published_at`, `updated_at`, asset `label`, `digest`, `uploader`).
- **References:**
  - [REST API — releases](https://docs.github.com/v3/repos/releases)
  - [REST API — release assets](https://docs.github.com/en/rest/releases/assets)
  - Asset `digest` is documented as `string | null` ([changelog](https://github.blog/changelog/2025-06-03-releases-now-expose-digests-for-release-assets/))
- **Fix applied:** `GithubReleases` now validates only the fields used by the downloader: `tag_name`, `assets[].name`, and `assets[].browser_download_url`.
- **Verify:** `uv run ublue-images tags refresh` against all repos listed in `tags.json`.

---

### F2 — `rpms.py` has no real CLI (Medium)

- [x] **Status**
- **Severity:** Medium
- **Symptom:** Any invocation runs the download path immediately. Verified before the Typer migration: `uv run src/ublue_images/rpms.py --help` and `uv run src/ublue_images/rpms.py --bogus` both start downloading (unknown args are ignored by Python when not parsed).
- **Location:** Fixed in `src/ublue_images/cli.py`; command implementation remains in `src/ublue_images/rpms.py`.
- **Impact:** Accidental runs, no `--help`, inconsistent with `tags.py`.
- **Fix applied:** `ublue-images rpms download` is a Typer subcommand; `ublue-images rpms` shows help instead of downloading.
- **Verify:** `uv run ublue-images rpms --help` prints usage and exits 0 without network I/O; unknown args exit non-zero.

---

### F3 — `tags.py` CLI: no required action, non-exclusive flags (Medium)

- [x] **Status**
- **Severity:** Medium
- **Symptom:**
  - Before the Typer migration, `uv run src/ublue_images/tags.py` (no args) exited **0** and performed **no work**.
  - `--refresh` and `--download` are not mutually exclusive; `--refresh --download` runs only refresh (`elif` chain).
- **Location:** Fixed in `src/ublue_images/cli.py`; command implementations remain in `src/ublue_images/tags.py`.
- **References:** [Typer subcommands](https://typer.tiangolo.com/tutorial/subcommands/), [Typer packaging](https://typer.tiangolo.com/tutorial/package/)
- **Fix applied:** `ublue-images tags refresh` and `ublue-images tags download` are explicit Typer subcommands; `ublue-images tags` shows help.
- **Verify:** `uv run ublue-images tags --help` prints help; documented behavior for supported subcommands is explicit.

---

### F4 — Download deletes output directory before any successful fetch (Medium)

- [ ] **Status**
- **Severity:** Medium
- **Symptom:** On failure mid-run, `files/dnf/rpms` or `files/dnf/tags` may be empty or partial while the recipe still expects RPMs (`recipes/_kinoite-dnf.yml`: `rpms/protonmail-bridge.rpm`, `tags/dbeaver.rpm`).
- **Location:** `download_files()` in `github_release_download.py` (`shutil.rmtree` then per-file download).
- **Suggested fix:**
  - Download to a temp directory (or write each file to `*.part` then rename), then atomic replace/rename into `output`.
  - Or remove tree only after all enabled downloads succeed.
- **Verify:** Simulate HTTP failure on second item; previous outputs or temp dir should remain recoverable.

---

### F5 — HTTP: no timeouts, full buffering in memory (Medium)

- [x] **Status**
- **Severity:** Medium
- **Symptom:** `requests.get(url)` with default `timeout=None` can hang indefinitely; `_download()` loads entire RPM into memory via `response.content`.
- **Location:** `get_latest_release()`, `_download()`, `download_file_to_local_dir()` in `github_release_download.py`
- **References:** [Requests timeouts](https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts), [streaming with `iter_content`](https://requests.readthedocs.io/en/latest/user/advanced/#body-content-workflow)
- **Fix applied:** API and asset requests pass explicit connect/read timeouts; downloads use `stream=True` and `iter_content(chunk_size=...)`.
- **Future option:** A shared `requests.Session` with retries could still improve transient failure handling.
- **Verify:** Large RPM download uses bounded memory; hung server fails within timeout.

---

### F6 — GitHub API: no auth headers (Low / operational)

- [ ] **Status**
- **Severity:** Low (until rate-limited)
- **Symptom:** Unauthenticated `GET /repos/{owner}/{repo}/releases/latest` shares a low rate limit on GitHub Actions IPs.
- **Location:** `get_latest_release()`
- **Suggested fix:** Optional `GITHUB_TOKEN` / `GH_TOKEN` from env (`Authorization: Bearer`, `Accept: application/vnd.github+json`, API version header per [GitHub docs](https://docs.github.com/v3/repos/releases)).
- **Verify:** Refresh still works without token locally; CI uses `GITHUB_TOKEN` when present.

---

### F7 — RPM asset selection heuristic (Low)

- [ ] **Status**
- **Severity:** Low
- **Symptom:** `get_rpm_download_url()` picks the first asset whose name ends with `x86_64.rpm`. This matches the current DBeaver asset name (`...linux-x86_64.rpm`), but multiple matching assets could still pick the wrong file, and nonstandard RPM names could raise `ValueError`.
- **Location:** `get_rpm_download_url()` in `github_release_download.py`
- **Current data:** `tags.json` DBeaver asset name pattern: `dbeaver-ce-26.1.1-linux-x86_64.rpm`.
- **Suggested fix:** Prefer explicit `name` glob/regex per item in `tags.json`, or match `x86_64` + `.rpm` more deliberately; fail with asset list in error message.
- **Verify:** Refresh for each configured repo resolves expected RPM URL.

---

### F8 — Dead / legacy code and dependencies (Low)

- [ ] **Status**
- **Severity:** Low
- **Symptom:** `github_release_download.py` still calls `load_dotenv()`, and `pyproject.toml` still depends on `python-dotenv`, but no download-specific environment variables are documented or used.
- **Already cleaned up:** The previous `joblib` dependency is no longer present in `pyproject.toml`.
- **Suggested fix:** Remove `load_dotenv()` and `python-dotenv`, unless F6 adds documented token loading from environment.
- **Verify:** `uv run` / CI still pass; lockfile updated if deps removed.

---

### F9 — `refresh_tags()` all-or-nothing behavior is implicit (Low)

- [-] **Status**
- **Severity:** Low
- **Current behavior:** `refresh_tags()` updates items in memory and writes `tags.json` only after the loop completes. A failure before `write_text()` leaves the on-disk file unchanged.
- **Decision:** Defer per-item recovery for now. Failing the whole refresh is reasonable while there is only one tagged release item and CI should surface broken release metadata.
- **Future option:** If more repos are added, decide whether one broken repo should block all tag updates or whether successful items should still be written.
- **Verify if revisited:** One broken repo in `tags.json` behaves according to the documented CI policy.

---

## CLI reference (as reviewed)

| Command | Documented args | Actual behavior |
| --- | --- | --- |
| `ublue-images tags` | `refresh`, `download`, `--help` | Grouped Typer subcommands |
| `ublue-images rpms` | `download`, `--help` | Grouped Typer subcommands |

CI usage:

- `uv run ublue-images tags refresh` (update-tags job)
- `uv run ublue-images rpms download` (cache miss)
- `uv run ublue-images tags download` (cache miss)

---

## Suggested fix order

1. **F4** — Prevent failed downloads from leaving partial RPM directories behind.
2. **F6** — Add optional GitHub API auth headers before rate limits become noisy in CI.
3. **F7** — Make RPM asset selection explicit before adding more tagged release repos.
4. **F8** — Remove unused dotenv loading, unless F6 uses it intentionally.

---

## Changelog (fixes)

| Date | Finding | Notes |
| --- | --- | --- |
| 2026-06-10 | F1 | Minimal `models/github.py`; full snapshot in `github_raw.py` via `just github-release-download`. |
| 2026-06-10 | F5 | Added explicit request timeouts and streamed file downloads with `iter_content()`. |
| 2026-07-05 | F2 | Added Typer CLI entrypoint with `ublue-images rpms download`. |
| 2026-07-05 | F3 | Added Typer subcommands for `ublue-images tags refresh` and `ublue-images tags download`. |
| 2026-07-05 | F9 | Deferred per-item recovery; documented current all-or-nothing refresh behavior. |

_Add a row when a finding is fixed (PR link optional)._
