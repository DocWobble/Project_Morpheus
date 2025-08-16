#!/usr/bin/env python3
"""Automatically merge aligned pull requests.

This utility rebases each open PR labeled "aligned" onto ``main``.
If tests invoked via ``scripts/run_tests.sh`` succeed, the PR is
merged. Otherwise the PR receives a ``merge-failed`` label.

Usage:
    python scripts/auto_merge.py --repo <owner/repo> [--token <token>]

Environment variables:
    GITHUB_REPOSITORY  Repository in "owner/repo" form (fallback for --repo)
    GITHUB_TOKEN       GitHub token with `repo` scope (fallback for --token)
"""
from __future__ import annotations

import argparse
import os
import subprocess
from typing import Iterable

import requests


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def _request(method: str, url: str, token: str | None, **kwargs) -> requests.Response:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    response = requests.request(method, url, headers=headers, **kwargs)
    response.raise_for_status()
    return response


def fetch_aligned_prs(repo: str, token: str | None) -> list[dict]:
    """Return open pull requests labeled ``aligned``."""
    url = f"https://api.github.com/repos/{repo}/pulls"
    params = {"state": "open", "per_page": 100}
    prs: list[dict] = []
    while url:
        response = _request("get", url, token, params=params)
        for pr in response.json():
            labels = {label["name"] for label in pr.get("labels", [])}
            if "aligned" in labels:
                prs.append(pr)
        url = response.links.get("next", {}).get("url")
        params = None
    return prs


def add_label(repo: str, number: int, label: str, token: str | None) -> None:
    """Attach *label* to pull request *number*."""
    url = f"https://api.github.com/repos/{repo}/issues/{number}/labels"
    _request("post", url, token, json={"labels": [label]})


def merge_pr(repo: str, number: int, token: str | None) -> None:
    """Merge pull request *number*."""
    url = f"https://api.github.com/repos/{repo}/pulls/{number}/merge"
    _request("put", url, token, json={"merge_method": "merge"})


# ---------------------------------------------------------------------------
# Local git + test helpers
# ---------------------------------------------------------------------------

def run(cmd: Iterable[str]) -> None:
    """Run *cmd* and raise :class:`CalledProcessError` on failure."""
    subprocess.run(list(cmd), check=True)


def process_pr(pr: dict, repo: str, token: str | None) -> None:
    """Rebase, test, and merge a single pull request."""
    number = pr["number"]
    head_ref = pr["head"]["ref"]
    local_branch = f"pr-{number}"
    try:
        run(["git", "fetch", "origin", f"pull/{number}/head:{local_branch}"])
        run(["git", "checkout", local_branch])
        run(["git", "rebase", "origin/main"])
        run(["scripts/run_tests.sh"])
        run([
            "git",
            "push",
            "--force-with-lease",
            "origin",
            f"{local_branch}:{head_ref}",
        ])
        merge_pr(repo, number, token)
    except subprocess.CalledProcessError:
        add_label(repo, number, "merge-failed", token)
    except requests.HTTPError:
        add_label(repo, number, "merge-failed", token)
    finally:
        run(["git", "checkout", "main"])
        subprocess.run(["git", "branch", "-D", local_branch], check=False)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Automatically merge aligned PRs")
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY"), help="Repository in 'owner/repo' form")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token with access to the repo")
    args = parser.parse_args()

    if not args.repo:
        raise SystemExit("Repository must be provided via --repo or GITHUB_REPOSITORY")

    prs = fetch_aligned_prs(args.repo, args.token)
    for pr in prs:
        process_pr(pr, args.repo, args.token)


if __name__ == "__main__":
    main()
