# 🤖 AI Code Reviewer

An automated GitHub Pull Request review bot powered by free LLMs (Groq + Gemini Flash). Detects bugs, security vulnerabilities, performance issues, and more — posting inline comments directly on your PRs.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 📸 Demo

> Bot automatically reviews a PR and posts inline comments with severity labels

<!-- Add screenshot here after first successful PR review -->
![Demo Screenshot](docs/demo.png)

---

## ✨ Features

- **Automatic PR Reviews** — triggered instantly when a PR is opened or updated via GitHub Webhooks
- **Inline Comments** — posts comments directly on the relevant lines of code
- **Multi-Model Pipeline** — uses Groq (Llama 3.3 70B) as primary, Gemini 1.5 Flash as fallback
- **Structured Feedback** — categorizes issues as bug, security, performance, style, or maintainability
- **Severity Filtering** — only surfaces high and medium issues as inline comments, low issues in summary
- **Smart File Skipping** — ignores lock files, binaries, and auto-generated files
- **Summary Scorecard** — posts a summary comment with issue counts by category and severity
- **Large Diff Handling** — automatically chunks large diffs to stay within token limits
- **100% Free** — runs entirely on free-tier APIs with no paid models

---

## 🏗️ Architecture

```
GitHub PR Opened/Updated
        │
        ▼
  Webhook POST /webhook
  (FastAPI + HMAC verification)
        │
        ▼
  Parse Git Diff
  (filter irrelevant files)
        │
        ▼
  ┌─────────────────────┐
  │  Groq Llama 3.3 70B │  ← Primary
  └─────────────────────┘
        │ (on failure)
        ▼
  ┌─────────────────────┐
  │  Gemini 1.5 Flash   │  ← Fallback
  └─────────────────────┘
        │
        ▼
  Structured JSON Issues
  {file, line, severity, category, message}
        │
        ▼
  Post Inline PR Comments
  + Summary Scorecard
  via GitHub API
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A GitHub account
- Free API keys for [Groq](https://console.groq.com) and [Google AI Studio](https://aistudio.google.com)

### Installation

```bash
# Clone the repo
git clone https://github.com/your-username/ai-code-reviewer.git
cd ai-code-reviewer

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_TOKEN=your_github_personal_access_token
```

| Variable | Where to get it |
|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → Free signup |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| `GITHUB_WEBHOOK_SECRET` | Any random string — run `openssl rand -hex 20` |
| `GITHUB_TOKEN` | GitHub → Settings → Developer Settings → Personal Access Tokens (needs `repo` scope) |

### Running Locally

```bash
# Start the server
uvicorn app.main:app --reload --port 8000

# Expose to internet for GitHub webhooks (dev only)
ngrok http 8000
```

### Setting Up the GitHub Webhook

1. Go to your repository → **Settings** → **Webhooks** → **Add webhook**
2. Set **Payload URL** to `https://your-ngrok-url/webhook`
3. Set **Content type** to `application/json`
4. Set **Secret** to your `GITHUB_WEBHOOK_SECRET`
5. Select **Pull requests** event only
6. Click **Add webhook**

---

## 📁 Project Structure

```
ai-code-reviewer/
├── app/
│   ├── main.py            # FastAPI app + webhook endpoint
│   ├── github_client.py   # PR diff fetching + comment posting
│   ├── llm_client.py      # Groq + Gemini with fallback logic
│   ├── diff_parser.py     # Git diff parsing + file filtering
│   └── prompts.py         # LLM prompt templates
├── tests/
│   └── test_llm.py        # LLM review tests
├── .env                   # Environment variables (not committed)
├── requirements.txt
└── README.md
```

---

## 🔒 Security

- All webhook payloads are verified using HMAC-SHA256 signature validation
- GitHub token is scoped to `repo` only — no admin permissions required
- API keys are loaded from environment variables, never hardcoded

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI |
| Primary LLM | Groq — Llama 3.3 70B |
| Fallback LLM | Google Gemini 1.5 Flash |
| GitHub Integration | PyGithub |
| Diff Parsing | unidiff |
| Deployment | Fly.io |

---

## 🛣️ Roadmap

- [ ] Support for more languages (currently language-agnostic)
- [ ] Re-review on PR update (not just open)
- [ ] GitHub Actions integration (no server needed)
- [ ] Web dashboard to view review history
- [ ] Fine-tune prompts per language/framework

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

## 🙋 Author

Built by Roshal Dsouza(https://github.com/roshaldsouza) as a portfolio project.  
Feel free to open issues or PRs!
