from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional


LOCAL_TZ = timezone(timedelta(hours=8))
DEFAULT_FOLDER_GUID = "00000000_0000_0000_0000_000000000000"
DEFAULT_FOLDER_NAME = "默认"

SECRET_PATTERNS = [
    ("openai_api_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "generic_api_key_assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|secret[_-]?key|private[_-]?key)"
            r"\b\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{20,}"
        ),
    ),
]

TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".tsv"}
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WHITESPACE = re.compile(r"\s+")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_utf8(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def epoch_ms_to_dt(value) -> Optional[datetime]:
    if value in (None, "", 0):
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=LOCAL_TZ)
    except (TypeError, ValueError, OSError):
        return None


def format_dt(dt: Optional[datetime]) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S %z") if dt else ""


def file_date_from_ms(*values) -> str:
    for value in values:
        dt = epoch_ms_to_dt(value)
        if dt:
            return dt.strftime("%Y-%m-%d")
    return "undated"


def parse_todo_time(value) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, (int, float)):
        return epoch_ms_to_dt(value)
    text = str(value).strip()
    for fmt in ("%b %d, %Y %H:%M:%S", "%B %d, %Y %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=LOCAL_TZ)
        except ValueError:
            pass
    return None


def format_todo_time(value) -> str:
    dt = parse_todo_time(value)
    return format_dt(dt) if dt else str(value or "")


def sanitize_filename_part(text: str, max_len: int = 64) -> str:
    text = WHITESPACE.sub(" ", (text or "").strip())
    text = INVALID_FILENAME_CHARS.sub("-", text)
    text = text.strip(" .-_")
    if not text:
        return "untitled"
    if len(text) > max_len:
        text = text[:max_len].rstrip(" .-_")
    return text or "untitled"


def has_secret_shape(text: str) -> bool:
    return any(pattern.search(text or "") for _, pattern in SECRET_PATTERNS)


def make_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 2
    while True:
        candidate = parent / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def yaml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if value is None:
        return '""'
    return json.dumps(str(value), ensure_ascii=False)


def frontmatter(items: list[tuple[str, object]]) -> str:
    lines = ["---"]
    for key, value in items:
        lines.append(f"{key}: {yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


class NoteHtmlToMarkdown(HTMLParser):
    def __init__(self, image_links: dict[str, str]):
        super().__init__(convert_charrefs=True)
        self.image_links = image_links
        self.parts: list[str] = []
        self.ignore_depth = 0
        self.link_stack: list[Optional[str]] = []

    def ensure_newline(self) -> None:
        if self.parts and not "".join(self.parts[-2:]).endswith("\n"):
            self.parts.append("\n")

    def append(self, text: str) -> None:
        if text:
            self.parts.append(text)

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        attrs_dict = {k.lower(): v for k, v in attrs if k}
        if tag in {"head", "script", "style"}:
            self.ignore_depth += 1
            return
        if self.ignore_depth:
            return
        if tag == "br":
            self.append("\n")
        elif tag in {"p", "div", "body"}:
            self.ensure_newline()
        elif tag == "li":
            self.ensure_newline()
            self.append("- ")
        elif tag in {"ul", "ol"}:
            self.ensure_newline()
        elif tag == "img":
            src = (attrs_dict.get("src") or "").strip()
            alt = sanitize_alt(attrs_dict.get("alt") or src)
            link = self.image_links.get(src) or self.image_links.get(src.strip("/"))
            if link:
                self.append(f"![{alt}]({link})")
            elif src:
                self.append(f"![{alt}]({src})")
        elif tag == "a":
            href = (attrs_dict.get("href") or "").strip()
            if href:
                self.append("[")
                self.link_stack.append(href)
            else:
                self.link_stack.append(None)
        elif tag == "input":
            input_type = (attrs_dict.get("type") or "").lower()
            if input_type == "checkbox":
                checked = "checked" in attrs_dict or attrs_dict.get("value") in {"true", "1", "checked"}
                self.ensure_newline()
                self.append("- [x] " if checked else "- [ ] ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"head", "script", "style"} and self.ignore_depth:
            self.ignore_depth -= 1
            return
        if self.ignore_depth:
            return
        if tag in {"p", "div", "li", "ul", "ol", "body"}:
            self.ensure_newline()
        elif tag == "a" and self.link_stack:
            href = self.link_stack.pop()
            if href:
                self.append(f"]({href})")

    def handle_data(self, data: str) -> None:
        if not self.ignore_depth:
            self.append(data)

    def text(self) -> str:
        result = "".join(self.parts).replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.rstrip() for line in result.split("\n")]
        result = "\n".join(lines)
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()


class PlainTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignore_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in {"head", "script", "style"}:
            self.ignore_depth += 1
        elif not self.ignore_depth and tag in {"br", "p", "div", "li"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"head", "script", "style"} and self.ignore_depth:
            self.ignore_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.ignore_depth:
            self.parts.append(data)

    def text(self) -> str:
        return WHITESPACE.sub(" ", "".join(self.parts)).strip()


def sanitize_alt(text: str) -> str:
    return (text or "image").replace("[", "(").replace("]", ")")


def html_to_markdown(text: str, image_links: dict[str, str]) -> str:
    parser = NoteHtmlToMarkdown(image_links)
    parser.feed(text or "")
    parser.close()
    return parser.text()


def html_to_plain(text: str) -> str:
    parser = PlainTextExtractor()
    parser.feed(text or "")
    parser.close()
    return parser.text()


def find_zip_match(zip_names: list[str], attachment: dict) -> Optional[str]:
    aid = str(attachment.get("attachmentId") or "")
    url = str(attachment.get("url") or "").strip("/")
    matches = [name for name in zip_names if (aid and aid in name) or (url and url in name)]
    if not matches:
        return None

    def score(name: str) -> tuple[int, int, str]:
        lower = name.lower()
        is_thumb = "_thumb" in lower
        has_url = bool(url and url in name)
        return (0 if has_url and not is_thumb else 1 if not is_thumb else 2, len(name), name)

    return sorted(matches, key=score)[0]


def attachment_destination(zip_name: str, attachment_id: str, used_names: set[str], attachments_dir: Path) -> Path:
    suffix = Path(zip_name).suffix or ".bin"
    is_thumb = "_thumb" in Path(zip_name).stem.lower()
    name = f"{attachment_id}_thumb{suffix}" if is_thumb else f"{attachment_id}{suffix}"
    name = sanitize_filename_part(name, max_len=120)
    if name in used_names:
        stem = Path(name).stem
        suffix = Path(name).suffix
        index = 2
        while f"{stem}-{index}{suffix}" in used_names:
            index += 1
        name = f"{stem}-{index}{suffix}"
    used_names.add(name)
    return attachments_dir / name


def copy_attachments(notes: list[dict], backup_dir: Path, attachments_dir: Path) -> tuple[dict[str, dict], list[dict], Counter]:
    zip_path = backup_dir / "files" / "file_backup.zip"
    attachment_map: dict[str, dict] = {}
    missing: list[dict] = []
    stats: Counter = Counter()
    used_names: set[str] = set()
    if not zip_path.exists():
        stats["missing_zip_file"] += 1
        for note in notes:
            rich_note = note.get("richNote") or {}
            for attachment in note.get("attachments") or []:
                missing.append({
                    "attachmentId": attachment.get("attachmentId"),
                    "noteId": rich_note.get("globalId") or rich_note.get("localId"),
                    "url": attachment.get("url"),
                })
        return attachment_map, missing, stats

    with zipfile.ZipFile(zip_path) as archive:
        zip_names = archive.namelist()
        for note in notes:
            rich_note = note.get("richNote") or {}
            note_id = rich_note.get("globalId") or rich_note.get("localId")
            for attachment in note.get("attachments") or []:
                aid = str(attachment.get("attachmentId") or "")
                if not aid:
                    stats["missing_attachment_id"] += 1
                    continue
                match = find_zip_match(zip_names, attachment)
                if not match:
                    stats["missing_zip_match"] += 1
                    missing.append({"attachmentId": aid, "noteId": note_id, "url": attachment.get("url")})
                    continue
                dest = attachment_destination(match, aid, used_names, attachments_dir)
                with archive.open(match) as source, dest.open("wb") as target:
                    shutil.copyfileobj(source, target)
                kind = "thumb" if "_thumb" in Path(match).stem.lower() else "file"
                stats[f"copied_{kind}"] += 1
                attachment_map[aid] = {"path": dest, "zip_name": match, "note_id": note_id}
    return attachment_map, missing, stats


def relative_markdown_path(from_file: Path, target: Path) -> str:
    return os.path.relpath(target, start=from_file.parent).replace(os.sep, "/")


def build_note_image_links(note_file: Path, note: dict, attachment_map: dict[str, dict]) -> dict[str, str]:
    links: dict[str, str] = {}
    for attachment in note.get("attachments") or []:
        aid = str(attachment.get("attachmentId") or "")
        if aid not in attachment_map:
            continue
        rel = relative_markdown_path(note_file, attachment_map[aid]["path"])
        links[aid] = rel
        url = str(attachment.get("url") or "").strip("/")
        if url:
            links[url] = rel
            links["/" + url] = rel
    return links


def folder_lookup(folders: list[dict]) -> dict[str, str]:
    result = {DEFAULT_FOLDER_GUID: DEFAULT_FOLDER_NAME}
    for folder in folders:
        guid = folder.get("guid")
        name = folder.get("name") or DEFAULT_FOLDER_NAME
        if guid:
            if has_secret_shape(name):
                result[guid] = f"folder-{sanitize_filename_part(str(guid), max_len=12)}"
            else:
                result[guid] = sanitize_filename_part(name, max_len=48)
    return result


def note_filename(note: dict, folder_dir: Path, index: int) -> Path:
    rich_note = note.get("richNote") or {}
    local_id = sanitize_filename_part(str(rich_note.get("localId") or rich_note.get("globalId") or f"{index:04d}"), max_len=32)
    date = file_date_from_ms(rich_note.get("createTime"), rich_note.get("updateTime"), rich_note.get("timestamp"))
    return make_unique_path(folder_dir / f"{date}-note-{local_id}.md")


def write_notes(
    notes: list[dict],
    folders: list[dict],
    attachment_map: dict[str, dict],
    notes_dir: Path,
    backup_id: str,
) -> tuple[list[Path], Counter]:
    folders_by_guid = folder_lookup(folders)
    paths: list[Path] = []
    stats: Counter = Counter()
    sorted_notes = sorted(
        notes,
        key=lambda item: ((item.get("richNote") or {}).get("createTime") or 0, (item.get("richNote") or {}).get("localId") or 0),
    )
    for index, note in enumerate(sorted_notes, 1):
        rich_note = note.get("richNote") or {}
        folder_guid = rich_note.get("folderGuid") or DEFAULT_FOLDER_GUID
        folder_name = folders_by_guid.get(folder_guid, DEFAULT_FOLDER_NAME)
        folder_dir = notes_dir / folder_name
        folder_dir.mkdir(parents=True, exist_ok=True)
        path = note_filename(note, folder_dir, index)
        image_links = build_note_image_links(path, note, attachment_map)
        body = html_to_markdown(rich_note.get("htmlText") or rich_note.get("rawText") or rich_note.get("text") or "", image_links)
        title = (rich_note.get("title") or html_to_plain(rich_note.get("htmlText") or "") or "Untitled").strip()
        metadata = frontmatter([
            ("source", "OnePlus/Oppo ColorOS Notes backup"),
            ("backup_id", backup_id),
            ("type", "note"),
            ("title", title),
            ("folder", folder_name),
            ("folder_guid", folder_guid),
            ("deleted", bool(rich_note.get("deleted"))),
            ("state", rich_note.get("state", "")),
            ("global_id", rich_note.get("globalId", "")),
            ("local_id", rich_note.get("localId", "")),
            ("created", format_dt(epoch_ms_to_dt(rich_note.get("createTime")))),
            ("updated", format_dt(epoch_ms_to_dt(rich_note.get("updateTime")))),
            ("attachment_count", len(note.get("attachments") or [])),
        ])
        content = metadata + f"# {title}\n\n" + (body + "\n" if body else "_(empty note)_\n")
        write_utf8(path, content)
        paths.append(path)
        stats[folder_name] += 1
    return paths, stats


def todo_line(todo: dict) -> str:
    content = WHITESPACE.sub(" ", str(todo.get("mContent") or "").strip()) or "(empty todo)"
    suffix = []
    for label, key in [
        ("created", "mCreateTime"),
        ("updated", "mUpdateTime"),
    ]:
        value = format_todo_time(todo.get(key))
        if value:
            suffix.append(f"{label}: {value}")
    if todo.get("mStatus"):
        suffix.append(f"status: {todo.get('mStatus')}")
    if todo.get("mLocalId") not in (None, ""):
        suffix.append(f"localId: {todo.get('mLocalId')}")
    if todo.get("mGlobalId"):
        suffix.append(f"globalId: {todo.get('mGlobalId')}")
    meta = " ; ".join(suffix)
    return f"- [ ] {content}" + (f"  <!-- {meta} -->" if meta else "")


def write_todos(todos: list[dict], todos_dir: Path, backup_id: str) -> tuple[Path, Path, Counter]:
    active = [todo for todo in todos if not todo.get("mIsDelete")]
    deleted = [todo for todo in todos if todo.get("mIsDelete")]
    stats = Counter({"active": len(active), "deleted": len(deleted), "total": len(todos)})

    def sort_key(todo: dict):
        dt = parse_todo_time(todo.get("mCreateTime"))
        return (dt or datetime.min.replace(tzinfo=LOCAL_TZ), str(todo.get("mLocalId") or ""))

    active_path = todos_dir / "待办.md"
    deleted_path = todos_dir / "待办-已删除.md"
    active_content = frontmatter([
        ("source", "OnePlus/Oppo ColorOS Notes backup"),
        ("backup_id", backup_id),
        ("type", "todo-list"),
        ("deleted", False),
        ("count", len(active)),
    ])
    active_content += "# 待办\n\n" + "\n".join(todo_line(todo) for todo in sorted(active, key=sort_key)) + "\n"
    write_utf8(active_path, active_content)

    deleted_content = frontmatter([
        ("source", "OnePlus/Oppo ColorOS Notes backup"),
        ("backup_id", backup_id),
        ("type", "todo-list"),
        ("deleted", True),
        ("count", len(deleted)),
    ])
    deleted_content += "# 待办-已删除\n\n" + "\n".join(todo_line(todo) for todo in sorted(deleted, key=sort_key)) + "\n"
    write_utf8(deleted_path, deleted_content)
    return active_path, deleted_path, stats


def scan_for_secrets(root: Path) -> list[dict]:
    findings: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                for line_no, line in enumerate(handle, 1):
                    for secret_type, pattern in SECRET_PATTERNS:
                        if pattern.search(line):
                            findings.append({
                                "type": secret_type,
                                "path": str(path.relative_to(root)).replace(os.sep, "/"),
                                "line": line_no,
                            })
        except OSError as exc:
            findings.append({"type": "scan_error", "path": str(path), "line": 0, "error": str(exc)})
    return findings


def write_report(
    report_file: Path,
    backup_dir: Path,
    export_root: Path,
    notes: list[dict],
    todos: list[dict],
    note_paths: list[Path],
    note_folder_stats: Counter,
    attachment_missing: list[dict],
    attachment_stats: Counter,
    todo_stats: Counter,
    secret_findings: list[dict],
) -> None:
    attachment_records = sum(len(note.get("attachments") or []) for note in notes)
    copied = attachment_stats.get("copied_thumb", 0) + attachment_stats.get("copied_file", 0)
    lines = [
        "# 导出报告",
        "",
        f"- Backup source: `{backup_dir}`",
        f"- Export target: `{export_root}`",
        f"- Notes exported: {len(note_paths)} / {len(notes)}",
        f"- Todos exported: {todo_stats['total']} / {len(todos)}",
        f"- Active todos: {todo_stats['active']}",
        f"- Deleted todos: {todo_stats['deleted']}",
        f"- Attachment records: {attachment_records}",
        f"- Attachments copied: {copied}",
        f"- Missing attachment matches: {len(attachment_missing)}",
        f"- Secret scan findings: {len(secret_findings)}",
        "",
        "## Note folders",
        "",
    ]
    for folder, count in sorted(note_folder_stats.items(), key=lambda item: item[0]):
        lines.append(f"- {folder}: {count}")
    lines += ["", "## Attachment stats", ""]
    for key, count in sorted(attachment_stats.items()):
        lines.append(f"- {key}: {count}")
    if attachment_missing:
        lines += ["", "## Missing attachments", ""]
        for item in attachment_missing:
            lines.append(f"- attachmentId={item.get('attachmentId')} noteId={item.get('noteId')} url={item.get('url')}")
    if secret_findings:
        lines += [
            "",
            "## Secret scan findings",
            "",
            "Potential secrets were found. Values are intentionally not shown.",
        ]
        for item in secret_findings:
            lines.append(f"- {item.get('type')}: {item.get('path')}:{item.get('line')}")
    write_utf8(report_file, "\n".join(lines) + "\n")


def ensure_backup_shape(backup_dir: Path) -> None:
    missing = [name for name in ["rich_note", "todo", "folder"] if not (backup_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Backup directory is missing required file(s): {', '.join(missing)}")


def ensure_safe_export_root(vault_dir: Path, export_root: Path) -> None:
    vault = vault_dir.resolve()
    target = export_root.resolve()
    if not str(target).lower().startswith(str(vault).lower() + os.sep.lower()):
        raise RuntimeError(f"Refusing to use export path outside vault: {target}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export ColorOS Notes backup files to Obsidian Markdown.")
    parser.add_argument("--backup-dir", required=True, type=Path, help="Path to the Note backup directory containing rich_note, todo, and folder.")
    parser.add_argument("--vault-dir", required=True, type=Path, help="Path to the Obsidian vault directory.")
    parser.add_argument("--backup-id", help="Backup id used in output path. Defaults to the parent folder name of --backup-dir.")
    parser.add_argument("--export-subdir", default="手机备份/一加备忘录", help="Subdirectory inside the vault for exports.")
    parser.add_argument("--replace", action="store_true", help="Replace the existing target export directory if it already exists.")
    parser.add_argument("--no-secret-scan", action="store_true", help="Skip local secret scanning. Avoid this unless the user explicitly asks.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backup_dir = args.backup_dir.resolve()
    vault_dir = args.vault_dir.resolve()
    backup_id = args.backup_id or backup_dir.parent.name
    export_root = vault_dir / Path(args.export_subdir) / backup_id
    notes_dir = export_root / "备忘录"
    todos_dir = export_root / "待办"
    attachments_dir = export_root / "附件"
    report_file = export_root / "导出报告.md"

    ensure_backup_shape(backup_dir)
    ensure_safe_export_root(vault_dir, export_root)
    if export_root.exists():
        if not args.replace:
            raise FileExistsError(f"Export target exists; rerun with --replace to overwrite: {export_root}")
        shutil.rmtree(export_root)
    notes_dir.mkdir(parents=True, exist_ok=True)
    todos_dir.mkdir(parents=True, exist_ok=True)
    attachments_dir.mkdir(parents=True, exist_ok=True)

    notes = read_json(backup_dir / "rich_note")
    todos = read_json(backup_dir / "todo")
    folders = read_json(backup_dir / "folder")

    attachment_map, attachment_missing, attachment_stats = copy_attachments(notes, backup_dir, attachments_dir)
    note_paths, note_folder_stats = write_notes(notes, folders, attachment_map, notes_dir, backup_id)
    _, _, todo_stats = write_todos(todos, todos_dir, backup_id)
    secret_findings = [] if args.no_secret_scan else scan_for_secrets(export_root)
    write_report(
        report_file,
        backup_dir,
        export_root,
        notes,
        todos,
        note_paths,
        note_folder_stats,
        attachment_missing,
        attachment_stats,
        todo_stats,
        secret_findings,
    )

    summary = {
        "export_root": str(export_root),
        "notes_exported": len(note_paths),
        "todos_exported": len(todos),
        "active_todos": todo_stats["active"],
        "deleted_todos": todo_stats["deleted"],
        "attachment_records": sum(len(note.get("attachments") or []) for note in notes),
        "attachments_copied": attachment_stats.get("copied_thumb", 0) + attachment_stats.get("copied_file", 0),
        "missing_attachments": len(attachment_missing),
        "secret_findings": len(secret_findings),
        "report": str(report_file),
    }
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 2 if secret_findings else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        raise SystemExit(1)
