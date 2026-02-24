import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

github_client = Github(os.getenv("GITHUB_TOKEN"))


def get_pr_diff(repo_name: str, pr_number: int) -> str:
    """Fetch the raw diff of a pull request."""
    try:
        repo = github_client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # Get diff via raw comparison
        comparison = repo.compare(pr.base.sha, pr.head.sha)
        
        # Build a unified diff string manually from file patches
        diff_parts = []
        for file in pr.get_files():
            if file.patch:  # some files (binary) won't have a patch
                diff_parts.append(f"--- a/{file.filename}")
                diff_parts.append(f"+++ b/{file.filename}")
                diff_parts.append(file.patch)

        return "\n".join(diff_parts)

    except Exception as e:
        print(f"Failed to fetch PR diff: {e}")
        return ""


def post_review_comments(repo_name: str, pr_number: int, issues: list[dict]):
    """Post inline comments on the PR for each issue found."""
    if not issues:
        post_summary_comment(repo_name, pr_number, [])
        return

    try:
        repo = github_client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        commit = repo.get_commit(pr.head.sha)

        posted = 0
        failed = 0

        for issue in issues:
            # Only post high and medium severity inline
            if issue.get("severity") == "low":
                continue

            try:
                pr.create_review_comment(
                    body=format_comment(issue),
                    commit=commit,
                    path=issue["file"],
                    line=issue["line"]
                )
                posted += 1
            except Exception as e:
                print(f"Could not post inline comment on {issue['file']} line {issue['line']}: {e}")
                failed += 1

        print(f"Posted {posted} inline comments, {failed} failed")

        # Always post a summary comment too
        post_summary_comment(repo_name, pr_number, issues)

    except Exception as e:
        print(f"Failed to post review comments: {e}")


def post_summary_comment(repo_name: str, pr_number: int, issues: list[dict]):
    """Post a summary comment with issue counts and scorecard."""
    try:
        repo = github_client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        if not issues:
            body = "## 🤖 AI Code Review\n\n✅ **No issues found!** Looks good to me."
        else:
            # Count by category
            counts = {}
            for issue in issues:
                cat = issue.get("category", "other")
                counts[cat] = counts.get(cat, 0) + 1

            # Count by severity
            high = sum(1 for i in issues if i.get("severity") == "high")
            medium = sum(1 for i in issues if i.get("severity") == "medium")
            low = sum(1 for i in issues if i.get("severity") == "low")

            # Build scorecard
            category_icons = {
                "bug": "🐛",
                "security": "🔒",
                "performance": "⚡",
                "style": "🎨",
                "maintainability": "🔧"
            }

            category_lines = "\n".join(
                f"| {category_icons.get(cat, '📌')} {cat.capitalize()} | {count} |"
                for cat, count in counts.items()
            )

            body = f"""## 🤖 AI Code Review Summary

| Severity | Count |
|----------|-------|
| 🔴 High | {high} |
| 🟡 Medium | {medium} |
| 🟢 Low | {low} |

| Category | Count |
|----------|-------|
{category_lines}

> Inline comments posted for high and medium severity issues.
> Powered by Groq (Llama 3.3) with Gemini Flash fallback.
"""

        pr.create_issue_comment(body)

    except Exception as e:
        print(f"Failed to post summary comment: {e}")


def format_comment(issue: dict) -> str:
    """Format a single issue as a markdown comment."""
    severity_icons = {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢"
    }
    category_icons = {
        "bug": "🐛",
        "security": "🔒",
        "performance": "⚡",
        "style": "🎨",
        "maintainability": "🔧"
    }

    icon = severity_icons.get(issue.get("severity", "low"), "📌")
    cat_icon = category_icons.get(issue.get("category", "other"), "📌")

    return f"""{icon} **{issue.get('severity', '').upper()} — {cat_icon} {issue.get('category', '').capitalize()}**

{issue.get('message', '')}"""