"""
Primitive, explicit I/O tools.

These tools are intended to replace the "universal actuator" terminal tool for RL and
agent operation by exposing a small, explicit action space:
- READ_FILE / WRITE_FILE / APPEND_FILE / PATCH_FILE
- LIST_DIR / STAT_PATH
- EXECUTE (structured command execution with explicit cwd + env allowlist)
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import shlex
import tempfile
from typing import Any, Dict, List, Optional, Sequence

from ..config import config


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _clamp_int(value: Any, *, minimum: int, maximum: int, default: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        return default
    return max(minimum, min(maximum, parsed))


def _resolve_path(path: str) -> Path:
    # Keep behavior permissive for now; callers can supply absolute or relative paths.
    return Path(path).expanduser()


def _sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """
    Atomically replace `path` with `data` (best-effort preserves existing permissions).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing_mode = path.stat().st_mode
    except Exception:
        existing_mode = None

    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if existing_mode is not None:
            try:
                os.chmod(tmp_path, existing_mode)
            except Exception:
                pass
        os.replace(tmp_path, path)
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)  # type: ignore[arg-type]
        except Exception:
            pass


@dataclass(frozen=True)
class _FileReadResult:
    content: str
    truncated: bool
    bytes_read: int


def _read_text_file(path: Path, *, encoding: str, max_bytes: int) -> _FileReadResult:
    data = path.read_bytes()
    if len(data) > max_bytes:
        data = data[:max_bytes]
        truncated = True
    else:
        truncated = False
    return _FileReadResult(
        content=data.decode(encoding, errors="replace"),
        truncated=truncated,
        bytes_read=len(data),
    )


class ReadFileTool:
    @property
    def name(self) -> str:
        return "READ_FILE"

    @property
    def description(self) -> str:
        return (
            "Read a UTF-8 (or specified encoding) text file and return its contents. "
            "Use this instead of running `cat` via EXECUTE."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "encoding": {"type": "string", "description": "Text encoding (default: utf-8)", "default": "utf-8"},
                "max_bytes": {
                    "type": "integer",
                    "description": "Maximum bytes to read (default: 200000)",
                    "default": 200000,
                    "minimum": 1,
                    "maximum": 5_000_000,
                },
            },
            "required": ["path"],
        }

    def execute(self, path: str, encoding: str = "utf-8", max_bytes: int = 200000, **_: Any) -> Dict[str, Any]:
        try:
            resolved = _resolve_path(path)
            if not resolved.exists():
                return {"success": False, "error": "not_found", "path": str(resolved)}
            if not resolved.is_file():
                return {"success": False, "error": "not_a_file", "path": str(resolved)}

            max_bytes_i = _clamp_int(max_bytes, minimum=1, maximum=5_000_000, default=200000)
            read_result = _read_text_file(resolved, encoding=encoding or "utf-8", max_bytes=max_bytes_i)
            return {
                "success": True,
                "path": str(resolved),
                "content": read_result.content,
                "truncated": read_result.truncated,
                "bytes_read": read_result.bytes_read,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "path": _safe_str(path)}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"READ_FILE error: {result.get('error')} ({result.get('path')})"
        suffix = " (truncated)" if result.get("truncated") else ""
        return f"READ_FILE: {result.get('path')} ({result.get('bytes_read')} bytes){suffix}\n\n{result.get('content','')}"


class WriteFileTool:
    @property
    def name(self) -> str:
        return "WRITE_FILE"

    @property
    def description(self) -> str:
        return "Write a text file. Use this instead of `cat > file` via EXECUTE."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Full file contents to write"},
                "encoding": {"type": "string", "description": "Text encoding (default: utf-8)", "default": "utf-8"},
                "mkdirs": {"type": "boolean", "description": "Create parent directories if needed", "default": True},
                "overwrite": {"type": "boolean", "description": "Overwrite if file exists", "default": True},
            },
            "required": ["path", "content"],
        }

    def execute(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        mkdirs: bool = True,
        overwrite: bool = True,
        **_: Any,
    ) -> Dict[str, Any]:
        try:
            resolved = _resolve_path(path)
            if mkdirs:
                resolved.parent.mkdir(parents=True, exist_ok=True)
            if resolved.exists() and not overwrite:
                return {"success": False, "error": "exists", "path": str(resolved)}

            data = (content if isinstance(content, str) else _safe_str(content)).encode(encoding or "utf-8")
            resolved.write_bytes(data)
            return {"success": True, "path": str(resolved), "bytes_written": len(data)}
        except Exception as e:
            return {"success": False, "error": str(e), "path": _safe_str(path)}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"WRITE_FILE error: {result.get('error')} ({result.get('path')})"
        return f"WRITE_FILE: wrote {result.get('bytes_written')} bytes to {result.get('path')}"


class AppendFileTool:
    @property
    def name(self) -> str:
        return "APPEND_FILE"

    @property
    def description(self) -> str:
        return "Append text to a file (creates it if missing)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to append to"},
                "content": {"type": "string", "description": "Text to append"},
                "encoding": {"type": "string", "description": "Text encoding (default: utf-8)", "default": "utf-8"},
                "mkdirs": {"type": "boolean", "description": "Create parent directories if needed", "default": True},
            },
            "required": ["path", "content"],
        }

    def execute(self, path: str, content: str, encoding: str = "utf-8", mkdirs: bool = True, **_: Any) -> Dict[str, Any]:
        try:
            resolved = _resolve_path(path)
            if mkdirs:
                resolved.parent.mkdir(parents=True, exist_ok=True)

            data = (content if isinstance(content, str) else _safe_str(content)).encode(encoding or "utf-8")
            with resolved.open("ab") as f:
                f.write(data)
            return {"success": True, "path": str(resolved), "bytes_appended": len(data)}
        except Exception as e:
            return {"success": False, "error": str(e), "path": _safe_str(path)}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"APPEND_FILE error: {result.get('error')} ({result.get('path')})"
        return f"APPEND_FILE: appended {result.get('bytes_appended')} bytes to {result.get('path')}"


class ListDirTool:
    @property
    def name(self) -> str:
        return "LIST_DIR"

    @property
    def description(self) -> str:
        return "List directory entries with basic metadata."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list", "default": "."},
                "limit": {"type": "integer", "description": "Maximum entries to return (default: 200)", "default": 200},
                "include_hidden": {"type": "boolean", "description": "Include dotfiles", "default": False},
            },
            "required": [],
        }

    def execute(self, path: str = ".", limit: int = 200, include_hidden: bool = False, **_: Any) -> Dict[str, Any]:
        try:
            resolved = _resolve_path(path)
            if not resolved.exists():
                return {"success": False, "error": "not_found", "path": str(resolved)}
            if not resolved.is_dir():
                return {"success": False, "error": "not_a_dir", "path": str(resolved)}

            limit_i = _clamp_int(limit, minimum=1, maximum=5000, default=200)
            entries: List[Dict[str, Any]] = []
            with os.scandir(resolved) as it:
                for dent in it:
                    if not include_hidden and dent.name.startswith("."):
                        continue
                    try:
                        stat = dent.stat(follow_symlinks=False)
                        is_dir = dent.is_dir(follow_symlinks=False)
                        is_file = dent.is_file(follow_symlinks=False)
                    except Exception:
                        stat = None
                        is_dir = False
                        is_file = False

                    entries.append(
                        {
                            "name": dent.name,
                            "path": str(Path(resolved, dent.name)),
                            "type": "dir" if is_dir else ("file" if is_file else "other"),
                            "size": int(getattr(stat, "st_size", 0) or 0),
                            "mtime": int(getattr(stat, "st_mtime", 0) or 0),
                            "mtime_iso": (
                                datetime.fromtimestamp(
                                    float(getattr(stat, "st_mtime", 0) or 0),
                                    tz=timezone.utc,
                                ).isoformat()
                                if stat is not None
                                else None
                            ),
                        }
                    )
                    if len(entries) >= limit_i:
                        break

            entries.sort(key=lambda e: (e.get("type") != "dir", e.get("name", "")))
            return {"success": True, "path": str(resolved), "entries": entries, "count": len(entries)}
        except Exception as e:
            return {"success": False, "error": str(e), "path": _safe_str(path), "entries": [], "count": 0}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"LIST_DIR error: {result.get('error')} ({result.get('path')})"
        lines = [f"LIST_DIR: {result.get('path')} ({result.get('count')} entries)"]
        for entry in result.get("entries", [])[:50]:
            mtime_iso = entry.get("mtime_iso")
            mtime_raw = entry.get("mtime")
            mtime_display = mtime_iso if isinstance(mtime_iso, str) and mtime_iso else _safe_str(mtime_raw)
            lines.append(
                f"- {entry.get('type')}: {entry.get('name')} ({entry.get('size')} bytes, mtime={mtime_display})"
            )
        if result.get("count", 0) > 50:
            lines.append(f"... ({int(result.get('count', 0)) - 50} more)")
        return "\n".join(lines)


class StatPathTool:
    @property
    def name(self) -> str:
        return "STAT_PATH"

    @property
    def description(self) -> str:
        return "Return filesystem stat metadata for a path."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to stat"}},
            "required": ["path"],
        }

    def execute(self, path: str, **_: Any) -> Dict[str, Any]:
        try:
            resolved = _resolve_path(path)
            if not resolved.exists():
                return {"success": False, "error": "not_found", "path": str(resolved)}
            st = resolved.lstat()
            kind = "dir" if resolved.is_dir() else ("file" if resolved.is_file() else "other")
            return {
                "success": True,
                "path": str(resolved),
                "type": kind,
                "size": int(st.st_size),
                "mode": int(st.st_mode),
                "mtime": float(st.st_mtime),
                "ctime": float(st.st_ctime),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "path": _safe_str(path)}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"STAT_PATH error: {result.get('error')} ({result.get('path')})"
        return (
            f"STAT_PATH: {result.get('path')} ({result.get('type')}, {result.get('size')} bytes, "
            f"mtime={result.get('mtime')})"
        )


class PatchFileTool:
    @property
    def name(self) -> str:
        return "PATCH_FILE"

    @property
    def description(self) -> str:
        return (
            "Apply a small edit to an existing text file without rewriting the full file. "
            "Prefer `edits` (line-range replacements) for deterministic patching."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to patch"},
                "encoding": {"type": "string", "description": "Text encoding (default: utf-8)", "default": "utf-8"},
                "expected_sha256": {
                    "type": "string",
                    "description": "Optional SHA256 precondition for the current file contents",
                },
                "create_backup": {"type": "boolean", "description": "Create a backup copy before patching", "default": False},
                "backup_suffix": {"type": "string", "description": "Backup suffix (default: .bak)", "default": ".bak"},
                "validate_only": {"type": "boolean", "description": "Validate patch but do not write changes", "default": False},
                "edits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start_line": {"type": "integer", "minimum": 1},
                            "end_line": {"type": "integer", "minimum": 0},
                            "replacement": {"type": "string"},
                        },
                        "required": ["start_line", "end_line", "replacement"],
                    },
                    "description": "List of line-range replacements (1-based, inclusive).",
                },
                "unified_diff": {
                    "type": "string",
                    "description": "Optional unified diff string to apply (fallback).",
                },
                "fuzz_lines": {
                    "type": "integer",
                    "description": "Fuzzy match window (+/- lines) for unified diff hunks (default: 3)",
                    "default": 3,
                    "minimum": 0,
                    "maximum": 50,
                },
            },
            "required": ["path"],
        }

    def execute(
        self,
        path: str,
        edits: Optional[List[Dict[str, Any]]] = None,
        unified_diff: Optional[str] = None,
        encoding: str = "utf-8",
        expected_sha256: Optional[str] = None,
        create_backup: bool = False,
        backup_suffix: str = ".bak",
        validate_only: bool = False,
        fuzz_lines: int = 3,
        **_: Any,
    ) -> Dict[str, Any]:
        try:
            resolved = _resolve_path(path)
            if not resolved.exists():
                return {"success": False, "error": "not_found", "path": str(resolved)}
            if not resolved.is_file():
                return {"success": False, "error": "not_a_file", "path": str(resolved)}

            original_bytes = resolved.read_bytes()
            old_sha = _sha256_bytes(original_bytes)
            if isinstance(expected_sha256, str) and expected_sha256 and expected_sha256 != old_sha:
                return {
                    "success": False,
                    "error": "sha256_mismatch",
                    "path": str(resolved),
                    "expected_sha256": expected_sha256,
                    "actual_sha256": old_sha,
                }

            if create_backup:
                backup = resolved.with_name(resolved.name + (backup_suffix if isinstance(backup_suffix, str) and backup_suffix else ".bak"))
                if not validate_only:
                    _atomic_write_bytes(backup, original_bytes)

            if edits:
                return self._apply_line_edits(resolved, edits, encoding=encoding, validate_only=validate_only, old_sha256=old_sha)
            if unified_diff and unified_diff.strip():
                fuzz = _clamp_int(fuzz_lines, minimum=0, maximum=50, default=3)
                return self._apply_unified_diff(resolved, unified_diff, encoding=encoding, validate_only=validate_only, fuzz_lines=fuzz, old_sha256=old_sha)
            return {"success": False, "error": "no_edits_provided", "path": str(resolved)}
        except Exception as e:
            return {"success": False, "error": str(e), "path": _safe_str(path)}

    def _apply_line_edits(
        self,
        path: Path,
        edits: List[Dict[str, Any]],
        *,
        encoding: str,
        validate_only: bool,
        old_sha256: str,
    ) -> Dict[str, Any]:
        original_text = path.read_text(encoding=encoding or "utf-8", errors="replace")
        original = original_text.splitlines(keepends=True)
        n_lines = len(original)

        normalized: List[Dict[str, Any]] = []
        for edit in edits:
            start = int(edit.get("start_line"))
            end = int(edit.get("end_line"))
            replacement = _safe_str(edit.get("replacement"))
            if start < 1:
                return {"success": False, "error": f"invalid_start_line:{start}", "path": str(path)}
            if start > n_lines + 1:
                return {
                    "success": False,
                    "error": f"start_line_out_of_range:{start}",
                    "path": str(path),
                    "n_lines": n_lines,
                }
            if end < start - 1:
                return {"success": False, "error": f"invalid_end_line:{end}", "path": str(path)}
            if end > n_lines:
                return {"success": False, "error": f"end_line_out_of_range:{end}", "path": str(path), "n_lines": n_lines}
            normalized.append({"start": start, "end": end, "replacement": replacement})

        # Apply in reverse order so earlier edits don't shift later line numbers.
        normalized.sort(key=lambda e: (e["start"], e["end"]), reverse=True)
        lines = list(original)
        for edit in normalized:
            start_idx = edit["start"] - 1
            end_idx = edit["end"]  # inclusive end_line -> slice end is +1, but end_idx already +1 by using end directly.
            replacement_lines = edit["replacement"].splitlines(keepends=True)
            lines[start_idx:end_idx] = replacement_lines

        new_text = "".join(lines)
        new_bytes = new_text.encode(encoding or "utf-8", errors="replace")
        new_sha = _sha256_bytes(new_bytes)
        if not validate_only:
            _atomic_write_bytes(path, new_bytes)
        return {
            "success": True,
            "path": str(path),
            "applied_edits": len(normalized),
            "bytes_written": len(new_bytes),
            "old_sha256": old_sha256,
            "new_sha256": new_sha,
            "validate_only": bool(validate_only),
        }

    def _apply_unified_diff(
        self,
        path: Path,
        unified_diff: str,
        *,
        encoding: str,
        validate_only: bool,
        fuzz_lines: int,
        old_sha256: str,
    ) -> Dict[str, Any]:
        original_text = path.read_text(encoding=encoding or "utf-8", errors="replace")
        original_lines = original_text.splitlines(keepends=True)

        parsed = self._parse_unified_diff(unified_diff)
        # Safety: enforce single-file patches that target `path` if headers are present.
        if parsed["targets"]:
            expected = str(path)
            targets = parsed["targets"]
            if len(targets) != 1:
                return {"success": False, "error": "unified_diff_multi_target", "path": str(path), "diff_targets": targets}
            target = targets[0]
            if target != expected and not target.endswith(expected):
                return {"success": False, "error": "unified_diff_target_mismatch", "path": str(path), "diff_target": target}

        ok, new_lines, applied_hunks, error = self._apply_hunks(original_lines, parsed["hunks"], fuzz_lines=fuzz_lines)
        if not ok or error:
            return {"success": False, "error": error or "patch_failed", "path": str(path), "applied_hunks": applied_hunks}

        new_text = "".join(new_lines)
        new_bytes = new_text.encode(encoding or "utf-8", errors="replace")
        new_sha = _sha256_bytes(new_bytes)
        if not validate_only:
            _atomic_write_bytes(path, new_bytes)

        return {
            "success": True,
            "path": str(path),
            "applied_hunks": applied_hunks,
            "bytes_written": len(new_bytes),
            "old_sha256": old_sha256,
            "new_sha256": new_sha,
            "validate_only": bool(validate_only),
        }

    def _parse_unified_diff(self, diff_text: str) -> Dict[str, Any]:
        targets: List[str] = []
        hunks: List[Dict[str, Any]] = []

        lines = diff_text.splitlines(keepends=True)
        i = 0
        # headers
        while i < len(lines):
            line = lines[i]
            if line.startswith("--- "):
                left = line.split(maxsplit=1)[1].strip() if len(line.split(maxsplit=1)) == 2 else ""
                i += 1
                if i < len(lines) and lines[i].startswith("+++ "):
                    right = lines[i].split(maxsplit=1)[1].strip() if len(lines[i].split(maxsplit=1)) == 2 else ""
                    for marker in (left, right):
                        marker_path = marker.split("\t")[0].strip()
                        if marker_path in ("", "/dev/null"):
                            continue
                        if marker_path.startswith(("a/", "b/")):
                            marker_path = marker_path[2:]
                        targets.append(marker_path)
                    i += 1
                    continue
            if line.startswith("@@ "):
                break
            i += 1

        # hunks
        while i < len(lines):
            header = lines[i]
            if not header.startswith("@@"):
                i += 1
                continue
            # @@ -l,c +l,c @@
            try:
                header_core = header.strip().split("@@")[1].strip()
                parts = header_core.split()
                old_part = parts[0]
                new_part = parts[1]
                old_start, old_count = self._parse_hunk_range(old_part)
                new_start, new_count = self._parse_hunk_range(new_part)
            except Exception:
                return {"targets": sorted(set(targets)), "hunks": [], "error": "invalid_hunk_header"}

            i += 1
            hunk_lines: List[str] = []
            while i < len(lines):
                l = lines[i]
                if l.startswith("@@"):
                    break
                if l.startswith("--- ") and (i + 1) < len(lines) and lines[i + 1].startswith("+++ "):
                    break
                hunk_lines.append(l)
                i += 1
            hunks.append(
                {
                    "old_start": old_start,
                    "old_count": old_count,
                    "new_start": new_start,
                    "new_count": new_count,
                    "lines": hunk_lines,
                }
            )

        return {"targets": sorted(set(targets)), "hunks": hunks, "error": None}

    def _parse_hunk_range(self, token: str) -> tuple[int, int]:
        # token like "-12,5" or "+3" (count omitted implies 1)
        token = token.strip()
        if not token or token[0] not in ("-", "+"):
            raise ValueError("invalid_range_token")
        token = token[1:]
        if "," in token:
            a, b = token.split(",", 1)
            return int(a), int(b)
        return int(token), 1

    def _apply_hunks(
        self,
        original_lines: List[str],
        hunks: List[Dict[str, Any]],
        *,
        fuzz_lines: int,
    ) -> tuple[bool, List[str], int, Optional[str]]:
        lines = list(original_lines)
        offset = 0
        applied = 0

        for hunk in hunks:
            old_start = int(hunk["old_start"])
            idx_expected = max(0, (old_start - 1) + offset)
            ok, new_lines, delta, err = self._apply_single_hunk(lines, idx_expected, hunk["lines"])
            if not ok and fuzz_lines > 0:
                found = False
                for d in range(1, fuzz_lines + 1):
                    for candidate in (idx_expected - d, idx_expected + d):
                        if candidate < 0:
                            continue
                        ok2, new_lines2, delta2, err2 = self._apply_single_hunk(lines, candidate, hunk["lines"])
                        if ok2:
                            ok, new_lines, delta, err = ok2, new_lines2, delta2, err2
                            found = True
                            break
                    if found:
                        break
            if not ok:
                return False, lines, applied, err or "hunk_failed"
            lines = new_lines
            offset += delta
            applied += 1

        return True, lines, applied, None

    def _apply_single_hunk(
        self,
        lines: List[str],
        start_index: int,
        hunk_lines: List[str],
    ) -> tuple[bool, List[str], int, Optional[str]]:
        idx = start_index
        consumed_start = idx
        consumed_end = idx
        out_segment: List[str] = []

        for raw in hunk_lines:
            if raw.startswith("\\ No newline at end of file"):
                continue
            if not raw:
                return False, lines, 0, "invalid_hunk_line"
            op = raw[0]
            payload = raw[1:]
            if op == " ":
                if idx >= len(lines) or lines[idx] != payload:
                    return False, lines, 0, "context_mismatch"
                out_segment.append(lines[idx])
                idx += 1
                consumed_end = idx
            elif op == "-":
                if idx >= len(lines) or lines[idx] != payload:
                    return False, lines, 0, "deletion_mismatch"
                idx += 1
                consumed_end = idx
            elif op == "+":
                out_segment.append(payload)
            else:
                return False, lines, 0, "invalid_hunk_prefix"

        new_lines = list(lines)
        new_lines[consumed_start:consumed_end] = out_segment
        delta = len(out_segment) - (consumed_end - consumed_start)
        return True, new_lines, delta, None

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"PATCH_FILE error: {result.get('error', result.get('stderr', 'unknown'))} ({result.get('path')})"
        if "applied_edits" in result:
            return f"PATCH_FILE: applied {result.get('applied_edits')} edit(s) to {result.get('path')}"
        if "applied_hunks" in result:
            return f"PATCH_FILE: applied {result.get('applied_hunks')} hunk(s) to {result.get('path')}"
        return f"PATCH_FILE: patched {result.get('path')}"


class ExecuteTool:
    @property
    def name(self) -> str:
        return "EXECUTE"

    @property
    def description(self) -> str:
        return (
            "Execute a command with an explicit working directory and explicit env allowlist. "
            "Use this for running builds/tests/scripts; use READ_FILE/WRITE_FILE/etc for file I/O."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "cmd": {"type": "string", "description": "Command to execute (single string)"},
                "cwd": {"type": "string", "description": "Working directory (default: current directory)"},
                "timeout": {
                    "type": "integer",
                    "description": "Timeout seconds (default: 60, max: 600)",
                    "default": 60,
                    "minimum": 1,
                    "maximum": 600,
                },
                "stdin": {"type": "string", "description": "Optional stdin to pass to the process"},
                "env_allowlist": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Names of env vars to pass through to the child process",
                },
            },
            "required": ["cmd"],
        }

    def execute(
        self,
        cmd: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
        stdin: Optional[str] = None,
        env_allowlist: Optional[Sequence[str]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        try:
            if not isinstance(cmd, str) or not cmd.strip():
                return {"success": False, "error": "cmd_required"}

            timeout_i = _clamp_int(timeout, minimum=1, maximum=600, default=60)
            workdir = Path(cwd).expanduser() if isinstance(cwd, str) and cwd.strip() else Path.cwd()
            if not workdir.exists() or not workdir.is_dir():
                return {"success": False, "error": "invalid_cwd", "cwd": str(workdir)}

            allowed = set([v for v in (env_allowlist or []) if isinstance(v, str) and v.strip()])
            # Always include PATH so the command can be resolved.
            allowed.add("PATH")
            env = {k: v for k, v in os.environ.items() if k in allowed}

            def _iter_shell_ops(command: str):
                """
                Yield shell operator tokens found outside of quotes.

                Conservative parser for bash-style operators. We don't attempt to fully parse bash;
                we just need to (a) detect dangerous constructs and (b) split chains/pipelines so
                each segment can be allowlisted.
                """
                s = str(command)
                i = 0
                in_s = False
                in_d = False
                esc = False
                while i < len(s):
                    ch = s[i]
                    if esc:
                        esc = False
                        i += 1
                        continue
                    if ch == "\\" and not in_s:
                        esc = True
                        i += 1
                        continue
                    if ch == "'" and not in_d:
                        in_s = not in_s
                        i += 1
                        continue
                    if ch == '"' and not in_s:
                        in_d = not in_d
                        i += 1
                        continue
                    if in_s or in_d:
                        i += 1
                        continue

                    # Subshell / command substitution / redirections are blocked under whitelist mode.
                    if s.startswith("$(", i):
                        yield "$("
                        i += 2
                        continue
                    if ch == "`":
                        yield "`"
                        i += 1
                        continue
                    if s.startswith(">>", i):
                        yield ">>"
                        i += 2
                        continue
                    if s.startswith("<<", i):
                        yield "<<"
                        i += 2
                        continue
                    if ch in (">", "<"):
                        yield ch
                        i += 1
                        continue

                    # Chaining operators
                    if s.startswith("&&", i):
                        yield "&&"
                        i += 2
                        continue
                    if s.startswith("||", i):
                        yield "||"
                        i += 2
                        continue
                    if s.startswith("|&", i):
                        yield "|&"
                        i += 2
                        continue
                    if ch == "|":
                        yield "|"
                        i += 1
                        continue
                    if ch == ";":
                        yield ";"
                        i += 1
                        continue
                    if ch == "&":
                        yield "&"
                        i += 1
                        continue

                    i += 1

            def _split_shell_chain(command: str) -> List[str]:
                """
                Split a command string by top-level chaining/pipeline operators (outside quotes).
                Returns list of segment strings (no operators).
                """
                s = str(command)
                segs: List[str] = []
                cur: List[str] = []
                i = 0
                in_s = False
                in_d = False
                esc = False
                saw_op = False
                while i < len(s):
                    ch = s[i]
                    if esc:
                        esc = False
                        cur.append(ch)
                        i += 1
                        continue
                    if ch == "\\" and not in_s:
                        esc = True
                        cur.append(ch)
                        i += 1
                        continue
                    if ch == "'" and not in_d:
                        in_s = not in_s
                        cur.append(ch)
                        i += 1
                        continue
                    if ch == '"' and not in_s:
                        in_d = not in_d
                        cur.append(ch)
                        i += 1
                        continue
                    if in_s or in_d:
                        cur.append(ch)
                        i += 1
                        continue

                    # operators: treat any of these as a split point (but keep parsing)
                    if s.startswith("&&", i) or s.startswith("||", i) or s.startswith("|&", i):
                        seg = "".join(cur).strip()
                        segs.append(seg)
                        cur = []
                        saw_op = True
                        i += 2
                        continue
                    if ch in ("|", ";", "&"):
                        seg = "".join(cur).strip()
                        segs.append(seg)
                        cur = []
                        saw_op = True
                        i += 1
                        continue

                    cur.append(ch)
                    i += 1

                tail = "".join(cur).strip()
                if tail or saw_op:
                    segs.append(tail)
                return segs

            def _base_command_for_segment(segment: str) -> str:
                base = ""
                try:
                    parts = shlex.split(segment.strip())
                    # Skip env var assignments like FOO=bar
                    for part in parts:
                        if "=" in part and not part.startswith(("./", "/")) and part.split("=", 1)[0].isidentifier():
                            continue
                        base = part
                        break
                except Exception:
                    base = segment.strip().split()[0] if segment.strip().split() else ""
                # Normalize paths so "/usr/bin/python3" matches "python3" allowlists.
                if "/" in base:
                    base = os.path.basename(base)
                return base

            # Optional command allowlist to reduce "universal actuator" collapse.
            # IMPORTANT: EXECUTE uses shell=True with bash. That means a single 'cmd' string can
            # chain multiple commands via operators like '|', '&&', ';', etc.
            # We must enforce the whitelist for EVERY segment, and block redirections/subshells.
            allowlist = getattr(config.tools, "execute_command_whitelist", None)
            if isinstance(allowlist, list) and allowlist:
                allowset = {str(x) for x in allowlist if isinstance(x, str) and x.strip()}

                ops = list(_iter_shell_ops(cmd))
                # Hard-block dangerous shell constructs when whitelist is active.
                blocked_ops = {"$(", "`", ">", "<", ">>", "<<"}
                if any(op in blocked_ops for op in ops):
                    return {
                        "success": False,
                        "error": "command_not_allowed",
                        "base_command": _base_command_for_segment(cmd),
                        "allowed_commands": list(allowlist),
                        "detail": "shell_operator_not_allowed",
                    }
                # Disallow backgrounding entirely (as it can outlive the sandboxed turn).
                if "&" in ops:
                    return {
                        "success": False,
                        "error": "command_not_allowed",
                        "base_command": _base_command_for_segment(cmd),
                        "allowed_commands": list(allowlist),
                        "detail": "background_operator_not_allowed",
                    }

                segments = _split_shell_chain(cmd)
                if not segments:
                    return {"success": False, "error": "cmd_required"}
                if any(not seg for seg in segments):
                    return {
                        "success": False,
                        "error": "command_not_allowed",
                        "base_command": _base_command_for_segment(cmd),
                        "allowed_commands": list(allowlist),
                        "detail": "empty_command_segment",
                    }
                bases = [_base_command_for_segment(seg) for seg in segments]
                bad = [b for b in bases if not b or b not in allowset]
                if bad:
                    # Keep base_command for backwards compat in ToolRegistry logging.
                    base0 = bases[0] if bases else ""
                    return {
                        "success": False,
                        "error": "command_not_allowed",
                        "base_command": base0,
                        "allowed_commands": list(allowlist),
                        "disallowed_commands": bad,
                    }

            proc = subprocess.run(
                cmd,
                cwd=str(workdir),
                env=env,
                input=(stdin.encode("utf-8") if isinstance(stdin, str) else None),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_i,
                shell=True,
                executable="/bin/bash",
            )
            return {
                "success": proc.returncode == 0,
                "cmd": cmd,
                "cwd": str(workdir),
                "exit_code": int(proc.returncode),
                "stdout": proc.stdout.decode("utf-8", errors="replace"),
                "stderr": proc.stderr.decode("utf-8", errors="replace"),
            }
        except subprocess.TimeoutExpired as e:
            return {
                "success": False,
                "error": "timeout",
                "cmd": cmd,
                "cwd": cwd,
                "stdout": (e.stdout.decode("utf-8", errors="replace") if e.stdout else ""),
                "stderr": (e.stderr.decode("utf-8", errors="replace") if e.stderr else ""),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "cmd": _safe_str(cmd), "cwd": _safe_str(cwd)}

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"EXECUTE error: {result.get('error')} (cmd={result.get('cmd')})"
        out = result.get("stdout", "") or ""
        err = result.get("stderr", "") or ""
        return (
            f"EXECUTE: exit_code={result.get('exit_code')} cwd={result.get('cwd')}\n"
            f"cmd: {result.get('cmd')}\n\n"
            f"stdout:\n{out}\n\nstderr:\n{err}"
        )
