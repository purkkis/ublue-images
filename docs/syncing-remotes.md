# Syncing GitHub and GitLab Remotes

This repo has two remotes:

| Remote          | URL                                                    | Branch        |
| --------------- | ------------------------------------------------------ | ------------- |
| `origin`        | `git@github.com:purkkis/ublue-kinoite.git`             | `main`        |
| `origin-gitlab` | `https://gitlab.purkkis.dev/purkkis/ublue-kinoite.git` | `main-gitlab` |

## Sync GitHub → GitLab

```bash
git checkout main
git pull origin main
git checkout main-gitlab
git merge main
git push origin-gitlab main-gitlab
```

## Sync GitLab → GitHub

```bash
git checkout main-gitlab
git pull origin-gitlab main-gitlab
git checkout main
git merge main-gitlab
git push origin main
```

## Quick One-Liner (GitHub → GitLab)

```bash
git fetch origin && git push origin-gitlab origin/main:main-gitlab
```

## Quick One-Liner (GitLab → GitHub)

```bash
git fetch origin-gitlab && git push origin origin-gitlab/main-gitlab:main
```
