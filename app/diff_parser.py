from unidiff import PatchSet

def parse_diff(raw_diff: str) -> list[dict]:
    """
    Parse raw git diff into chunks per file.
    Returns list of {file, diff_chunk, added_lines}
    """
    chunks = []

    try:
        patch = PatchSet(raw_diff)
    except Exception as e:
        print(f"Failed to parse diff: {e}")
        return []

    for patched_file in patch:
        # Skip files we don't want to review
        if should_skip_file(patched_file.path):
            continue

        file_diff = str(patched_file)
        added_lines = {
            line.target_line_no
            for hunk in patched_file
            for line in hunk
            if line.is_added and line.target_line_no
        }

        chunks.append({
            "file": patched_file.path,
            "diff_chunk": file_diff,
            "added_lines": added_lines
        })

    return chunks


def should_skip_file(path: str) -> bool:
    """Skip auto-generated or irrelevant files."""
    skip_extensions = [
        ".lock", ".min.js", ".min.css", ".svg",
        ".png", ".jpg", ".jpeg", ".gif", ".ico",
        ".woff", ".woff2", ".ttf"
    ]
    skip_filenames = [
        "package-lock.json", "yarn.lock", "poetry.lock",
        "requirements.txt", "Pipfile.lock"
    ]

    filename = path.split("/")[-1]

    if filename in skip_filenames:
        return True
    if any(path.endswith(ext) for ext in skip_extensions):
        return True

    return False