Git diff/patch guide for creating and applying patches

1) Create a patch from working changes
- To create a single-file patch of uncommitted changes:
  git diff path/to/file > mychange.patch

- To create a patch representing commits (recommended for series):
  git format-patch -n HEAD~3  # creates .patch files for last 3 commits

2) Inspect/validate a patch before applying
- Preview the patch:
  less mychange.patch

- Check that it applies cleanly (dry-run):
  git apply --check --verbose mychange.patch

3) Apply a patch
- Apply to working tree (does not create commit):
  git apply --index mychange.patch
  # use --index to update the index/staging area

- Apply and commit from mailbox-style patches (created with git format-patch):
  git am --signoff < 0001-my-patch.patch

4) Common --pNUM usage
- If a patch contains paths with a leading directory that doesn't match your tree, use -pN:
  git apply -p1 my.patch  # strips the first path component
  # Example: a/dir/file -> with -p1 becomes dir/file

5) Troubleshooting
- If git apply fails due to whitespace or context mismatch, try:
  git apply --reject --whitespace=fix my.patch
  # This produces .rej files you can inspect and manually apply

- If the patch was generated with git format-patch and includes commit metadata, use git am:
  git am 0001-*.patch

6) Best practices
- Prefer producing patches from commits (git format-patch) rather than raw diffs when sharing changes.
- Always run git apply --check before applying in a different tree.
- Keep patches small and self-contained; include a descriptive commit message if using git format-patch.
- Use git status and git diff to validate repository state before and after applying patches.



Unified diff example (mailbox-style patch header used by git format-patch):

From 4c2a4addd4b7f3a1234567890abcdef Mon Sep 17 00:00:00 2001
From: Author Name <author.email@example.com>
Date: Tue, 30 Dec 2025 12:45:00 +1000
Subject: [PATCH 0001/1] Add description of the change

---
 filename.txt | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/filename.txt b/filename.txt
index 4c2a4ad..d4b7f3a 100644
--- a/filename.txt
+++ b/filename.txt
@@ -1,3 +1,4 @@
-This is the original line.
+This is the new line.
+Another new line added.
 This line remains unchanged.

Notes:
- On Fedora, the 'applypatch' helper may not be present. Use 'git apply' or the 'patch' utility instead:
  - git apply --check my.patch
  - git apply --index my.patch
  - patch -p1 < my.patch
