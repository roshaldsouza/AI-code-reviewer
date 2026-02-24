import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.llm_client import review_diff

sample_diff = """
--- a/app.py
+++ b/app.py
@@ -1,5 +1,8 @@
+import subprocess
+
 def get_user(user_id):
-    return db.query(user_id)
+    cmd = f"SELECT * FROM users WHERE id = {user_id}"
+    result = subprocess.run(cmd, shell=True)
+    return result
"""

issues = review_diff(sample_diff)
print(f"Found {len(issues)} issues:")
for issue in issues:
    print(f"  [{issue['severity'].upper()}] {issue['category']} - line {issue['line']}: {issue['message']}")

from app.github_client import get_pr_diff

# Replace with your own public repo and a real PR number
diff = get_pr_diff("roshaldsouza/test-repo", 1)
print(f"Fetched diff: {len(diff)} characters")