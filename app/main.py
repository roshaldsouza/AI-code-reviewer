import os
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from app.github_client import get_pr_diff, post_review_comments
from app.diff_parser import parse_diff
from app.llm_client import review_diff

load_dotenv()

app = FastAPI(title="AI Code Reviewer")

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")


def verify_signature(payload: bytes, signature: str) -> bool:
    if not signature or not signature.startswith("sha256="):
        return False
    mac = hmac.new(
        key=WEBHOOK_SECRET.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    )
    return hmac.compare_digest(f"sha256={mac.hexdigest()}", signature)


async def process_pr(repo_name: str, pr_number: int):
    print(f"\n🔍 Starting review for {repo_name} PR #{pr_number}")
    raw_diff = get_pr_diff(repo_name, pr_number)
    if not raw_diff:
        print("❌ Empty diff, skipping review")
        return
    print(f"📄 Fetched diff: {len(raw_diff)} characters")
    chunks = parse_diff(raw_diff)
    if not chunks:
        print("❌ No reviewable files found")
        return
    print(f"📂 Found {len(chunks)} files to review")
    all_issues = []
    for chunk in chunks:
        print(f"  🔎 Reviewing {chunk['file']}...")
        issues = review_diff(chunk["diff_chunk"])
        for issue in issues:
            issue["file"] = chunk["file"]
        all_issues.extend(issues)
    print(f"✅ Found {len(all_issues)} total issues")
    post_review_comments(repo_name, pr_number, all_issues)
    print(f"💬 Review posted to PR #{pr_number}")


@app.get("/")
def health_check():
    return {"status": "AI Code Reviewer is running ✅"}


@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.body()
    #signature = request.headers.get("X-Hub-Signature-256", "")

    #if not verify_signature(payload, signature):
       # raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        return {"status": "ignored", "event": event}

    data = await request.json()
    action = data.get("action", "")
    if action not in ["opened", "synchronize"]:
        return {"status": "ignored", "action": action}

    repo_name = data["repository"]["full_name"]
    pr_number = data["pull_request"]["number"]
    print(f"📥 Received PR event: {action} for {repo_name} #{pr_number}")
    background_tasks.add_task(process_pr, repo_name, pr_number)
    return {"status": "review started", "pr": pr_number}