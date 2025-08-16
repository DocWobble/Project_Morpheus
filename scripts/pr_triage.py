#!/usr/bin/env python3
"""Triage open pull requests.

This utility classifies each open PR in a repository as either
"aligned" or "deprecated" based on the paths it modifies. A short
comment with the classification result is posted on the PR. In
addition, any pull request carrying a ``deprecated`` label is
automatically closed with a brief rationale comment.

Usage:
    python scripts/pr_triage.py --repo <owner/repo> [--token <token>]

Environment variables:
    GITHUB_REPOSITORY  Repository in "owner/repo" form (fallback for --repo)
    GITHUB_TOKEN       GitHub token with `repo` scope (fallback for --token)
"""
from __future__ import annotations

import argparse
import os
from typing import Iterable, List

import requests

# Paths that indicate work in deprecated areas of the codebase. Any PR
# modifying files under these paths will be classified as "deprecated".
DEPRECATED_PATHS: List[str] = [
    "ComfyUI/",
    "Oogabooga WebUI/",
]


def fetch_open_prs(repo: str, token: str | None) -> list[dict]:
    """Return all open pull requests for *repo*.

    Parameters
    ----------
    repo:
        Repository in ``owner/repo`` form.
    token:
        Optional GitHub token for authenticated requests.
    """
    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    params = {"state": "open", "per_page": 100}
    prs: list[dict] = []

    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        prs.extend(response.json())
        url = response.links.get("next", {}).get("url")
        params = None  # Subsequent pages already encoded in ``url``
    return prs


def fetch_pr_files(repo: str, number: int, token: str | None) -> list[str]:
    """Return a list of file paths changed in a pull request."""
    url = f"https://api.github.com/repos/{repo}/pulls/{number}/files"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    params = {"per_page": 100}
    files: list[str] = []

    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        files.extend(file["filename"] for file in response.json())
        url = response.links.get("next", {}).get("url")
        params = None
    return files


def classify_paths(paths: Iterable[str]) -> str:
    """Classify a set of paths as ``aligned`` or ``deprecated``."""
    for path in paths:
        if any(path.startswith(prefix) for prefix in DEPRECATED_PATHS):
            return "deprecated"
    return "aligned"


def post_comment(
    repo: str,
    number: int,
    body: str,
    token: str | None,
    *,
    dry_run: bool = False,
) -> None:
    """Post *body* as a comment on a pull request."""
    if dry_run:
        print(f"Would comment on PR #{number}: {body}")
        return

    if not token:
        raise RuntimeError("A GitHub token is required to post comments")

    url = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"token {token}"}
    response = requests.post(url, headers=headers, json={"body": body})
    response.raise_for_status()


def close_pr(repo: str, number: int, token: str | None, *, dry_run: bool = False) -> None:
    """Close a pull request via the GitHub API."""
    if dry_run:
        print(f"Would close PR #{number}")
        return

    if not token:
        raise RuntimeError("A GitHub token is required to close pull requests")

    url = f"https://api.github.com/repos/{repo}/pulls/{number}"
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"token {token}"}
    response = requests.patch(url, headers=headers, json={"state": "closed"})
    response.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify open pull requests")
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY"), help="Repository in 'owner/repo' form")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token with access to the repo")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without posting comments")
    args = parser.parse_args()

    if not args.repo:
        raise SystemExit("Repository must be provided via --repo or GITHUB_REPOSITORY")

    prs = fetch_open_prs(args.repo, args.token)
    for pr in prs:
        number = pr["number"]
        labels = {label["name"] for label in pr.get("labels", [])}
        if "deprecated" in labels:
            rationale = "Closing PR: feature superseded by streaming orchestrator design."
            post_comment(args.repo, number, rationale, args.token, dry_run=args.dry_run)
            close_pr(args.repo, number, args.token, dry_run=args.dry_run)
            continue

        files = fetch_pr_files(args.repo, number, args.token)
        classification = classify_paths(files)
        body = f"PR triage result: **{classification}**"
        post_comment(args.repo, number, body, args.token, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
