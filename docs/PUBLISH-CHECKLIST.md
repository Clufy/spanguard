# Publish checklist (external, human-only steps)

The CI, publish, and docs workflows in `.github/workflows/` are ready to run,
but a few one-time steps happen **outside the repo**, on GitHub.com and
PyPI.org, and only a human with the right account access can do them.

**No PyPI token is ever committed to this repository.** Publishing uses PyPI
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OpenID
Connect / OIDC): GitHub Actions proves its identity to PyPI at publish time
via a short-lived, workflow-scoped OIDC token, and PyPI exchanges that for
a one-time upload credential. There is no long-lived secret to create,
store, or rotate.

Do these steps in order:

## 1. Create the GitHub repo and push

Create a public GitHub repository — `spanguard/spanguard` if you have access
to that organization, otherwise substitute your own account/org as the
owner — and push this codebase to it:

```bash
git remote add origin https://github.com/<owner>/spanguard.git
git push -u origin master
```

## 2. Enable GitHub Pages

In the new repo: **Settings → Pages → Build and deployment → Source**, select
**GitHub Actions**. This lets `.github/workflows/docs.yml` deploy the mkdocs
site on every push to `master`/`main`. No branch or folder needs to be
selected — the workflow uploads the built site directly.

## 3. Register the PyPI Trusted Publisher

On [pypi.org](https://pypi.org), either:

- for a **new** project: go to
  [Publishing → Add a new pending publisher](https://pypi.org/manage/account/publishing/),
  or
- for an **existing** project you own: go to the project's
  **Settings → Publishing** page,

and add a GitHub publisher with:

| Field | Value |
|---|---|
| PyPI project name | `spanguard` |
| Owner | `<owner>` (the GitHub org/user from step 1) |
| Repository name | `spanguard` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

## 4. Create the `pypi` environment in repo settings

In the GitHub repo: **Settings → Environments → New environment**, name it
`pypi` (must match exactly — this is the `environment: pypi` referenced in
`.github/workflows/publish.yml`). Optionally add required reviewers or
restrict it to tag pushes for an extra manual-approval gate before a release
goes live.

## 5. Tag a release to trigger publish

```bash
git tag v0.1.0
git push origin v0.1.0
```

Pushing a tag matching `v*` triggers `.github/workflows/publish.yml`, which
builds the sdist/wheel with `uv build` and uploads them to PyPI via
`pypa/gh-action-pypi-publish` using the OIDC flow configured in steps 3–4.

## 6. Update placeholders to the real owner

`README.md` and `pyproject.toml` currently reference the placeholder owner
`spanguard/spanguard`. Once the repo exists under its real owner, update:

- `README.md` badge URLs (CI, PyPI, coverage, docs)
- `pyproject.toml` → `[project.urls]` → `Homepage` and `Documentation`

to point at the actual `<owner>/spanguard` GitHub path and the actual PyPI
package page, then commit and push.

## Summary

| Step | Where | One-time? |
|---|---|---|
| Create repo + push | GitHub | Yes |
| Enable Pages (source: GitHub Actions) | GitHub repo settings | Yes |
| Register Trusted Publisher | PyPI | Yes |
| Create `pypi` environment | GitHub repo settings | Yes |
| Tag `v0.1.0` | local → GitHub | Per release |
| Update badge/URL placeholders | this repo | Once, after step 1 |

No PyPI API token, password, or other secret needs to be created, stored in
GitHub Secrets, or committed anywhere for any of this to work.
