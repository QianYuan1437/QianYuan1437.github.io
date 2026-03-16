import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


USER = "QianYuan1437"
OUTPUT_PATH = Path("docs/repos-data.json")
API_VERSION = "2022-11-28"

MANUAL_PAGES = [
    {
        "repoName": "ArxivCBF",
        "name": "Arxiv每日更新",
        "desc": "控制障碍函数（CBF）相关论文每日更新与分栏浏览。",
        "url": "https://qianyuan1437.github.io/ArxivCBF/",
        "path": "/ArxivCBF/",
        "type": "研究",
        "icon": "🧠",
        "badge": "研究",
        "featured": True,
        "isFork": False,
    },
    {
        "repoName": "osssync",
        "name": "osssync",
        "desc": "对象存储同步工具，支持多种云存储服务间的文件同步。",
        "url": "https://github.com/QianYuan1437/osssync",
        "path": "/osssync/",
        "type": "工具",
        "icon": "🔧",
        "badge": "工具",
        "featured": True,
        "isFork": False,
    },
    {
        "repoName": "DOB-VS-ESO",
        "name": "DOB-VS-ESO",
        "desc": "DOB 与 ESO 相关项目页面导航。",
        "url": "https://qianyuan1437.github.io/DOB-VS-ESO/",
        "path": "/DOB-VS-ESO/",
        "type": "研究",
        "icon": "🧠",
        "badge": "研究",
        "featured": True,
        "isFork": False,
    },
]

TYPE_STYLE = {
    "内容": {"icon": "📰", "badge": "内容"},
    "工具": {"icon": "🔧", "badge": "工具"},
    "研究": {"icon": "🧠", "badge": "研究"},
}


def normalize_repo_name(value: str) -> str:
    return str(value or "").strip().lower()


def get_page_key(page: dict) -> str:
    return normalize_repo_name(page.get("repoName") or page.get("name"))


def infer_type(repo: dict) -> str:
    haystack = f"{repo.get('name', '')} {repo.get('description') or ''}".lower()
    if re.search(r"(tracker|arxiv|paper|research|robot|cbf|learning|control|dob|eso)", haystack):
        return "研究"
    if re.search(r"(monitor|tool|dashboard|script|sync|api|bot|oss)", haystack):
        return "工具"
    return "内容"


def repo_to_page(repo: dict) -> dict:
    repo_name = repo["name"]
    repo_url = repo.get("html_url") or f"https://github.com/{USER}/{repo_name}"
    is_user_site_repo = normalize_repo_name(repo_name) == f"{USER.lower()}.github.io"
    homepage = str(repo.get("homepage") or "").strip()
    page_url = homepage or (
        f"https://{USER.lower()}.github.io/"
        if is_user_site_repo
        else f"https://{USER.lower()}.github.io/{repo_name}/"
    )
    repo_type = infer_type(repo)
    style = TYPE_STYLE[repo_type]
    has_pages = bool(repo.get("has_pages"))
    return {
        "repoName": repo_name,
        "name": repo_name,
        "desc": repo.get("description") or "暂无仓库描述。",
        "url": page_url if has_pages else repo_url,
        "path": "/" if is_user_site_repo else f"/{repo_name}/",
        "type": repo_type,
        "icon": style["icon"],
        "badge": style["badge"],
        "featured": has_pages,
        "updated_at": repo.get("pushed_at") or repo.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        "isFork": bool(repo.get("fork")),
    }


def merge_manual_pages(repo_pages: list[dict]) -> list[dict]:
    manual_map = {get_page_key(page): page for page in MANUAL_PAGES}
    merged_pages = []
    for page in repo_pages:
        manual_page = manual_map.get(get_page_key(page))
        if not manual_page:
            merged_pages.append(page)
            continue
        merged_pages.append(
            {
                **page,
                **manual_page,
                "repoName": manual_page.get("repoName") or page.get("repoName"),
                "featured": bool(page.get("featured") or manual_page.get("featured")),
            }
        )

    existing_keys = {get_page_key(page) for page in merged_pages}
    for page in MANUAL_PAGES:
        if get_page_key(page) not in existing_keys:
            merged_pages.insert(0, dict(page))
    return merged_pages


def fetch_json(url: str, token: str | None) -> list[dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": f"{USER}-repo-card-sync",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def fetch_all_repos(user: str, token: str | None) -> list[dict]:
    all_repos = []
    for page in range(1, 11):
        query = urllib.parse.urlencode(
            {
                "type": "all",
                "per_page": 100,
                "sort": "updated",
                "page": page,
            }
        )
        url = f"https://api.github.com/users/{user}/repos?{query}"
        repos = fetch_json(url, token)
        if not isinstance(repos, list) or not repos:
            break
        all_repos.extend(repos)
        if len(repos) < 100:
            break

    unique_repos = []
    seen_keys = set()
    for repo in all_repos:
        key = str(repo.get("id") or repo.get("full_name") or repo.get("name") or "")
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        unique_repos.append(repo)
    return unique_repos


def main() -> None:
    token = os.getenv("GITHUB_TOKEN")
    repos = fetch_all_repos(USER, token)
    repo_pages = [repo_to_page(repo) for repo in repos]
    pages = merge_manual_pages(repo_pages)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages": pages,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(pages)} pages to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
