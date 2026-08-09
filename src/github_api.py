import requests
from src.i18n import __


def _extract_error_message(response):
    """Best-effort extraction of GitHub's error payload (message + errors[])."""
    try:
        j = response.json()
        details = j.get("message", "")
        for err in j.get("errors", []):
            field = err.get("field", "")
            msg = err.get("message", "")
            if field:
                details += f" [{field}: {msg}]"
            elif msg:
                details += f" {msg}"
        return details.strip() or response.text
    except Exception:
        return response.text


def create_pull_request(repo_info, github_token, title, body, head, base, timeout=30):
    """
    Creates a GitHub Pull Request via REST API.

    Returns (ok: bool, data: dict, http_status: int).
      - ok=True,  data={'url': html_url, 'number': n},  status=201
      - ok=False, data={'message': user-facing error},  status=401/422/other/0
    status 0 = network/connection failure (no HTTP response).
    """
    api_url = f"https://api.github.com/repos/{repo_info}/pulls"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {"title": title, "body": body, "head": head, "base": base}

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
        if response.status_code == 201:
            j = response.json()
            return True, {"url": j.get("html_url"), "number": j.get("number")}, 201

        return False, {"message": _extract_error_message(response)}, response.status_code

    except requests.exceptions.ConnectionError:
        return False, {"message": __("No internet connection. Cannot create the pull request.")}, 0
    except requests.exceptions.Timeout:
        return False, {"message": __("GitHub API timeout. Check your connection and try again.")}, 0
    except Exception as e:
        return False, {"message": __("Failed to connect to GitHub: {error}", error=str(e))}, 0


def check_existing_pr(repo_info, github_token, head_branch, timeout=15):
    """
    Check if there's already an open PR from *head_branch* to any base.

    Returns (exists: bool, pr_url: str | None, pr_number: int | None).
    """
    api_url = f"https://api.github.com/repos/{repo_info}/pulls"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    params = {"head": f"{repo_info.split('/')[0]}:{head_branch}", "state": "open"}
    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=timeout)
        if response.status_code == 200:
            prs = response.json()
            if prs:
                pr = prs[0]
                return True, pr.get("html_url"), pr.get("number")
        return False, None, None
    except Exception:
        return False, None, None
