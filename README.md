# OnePlus Notes to Obsidian

[简体中文](README.zh-CN.md)

A Codex skill and standard-library Python helper for exporting OnePlus/Oppo ColorOS Notes backups into an Obsidian vault.

The workflow reads the backup files commonly produced by the ColorOS/OnePlus backup tool:

- `rich_note`
- `todo`
- `folder`
- `files/file_backup.zip`

It converts rich notes to Markdown, writes Todo lists, copies referenced attachments, produces an export report, and scans generated text for common secret patterns to help prevent sensitive note content from being accidentally uploaded to an open-source repository or GitHub. Git commit and push are separate explicit steps.

## Features

- One Markdown file per rich note.
- Separate active and deleted Todo lists.
- HTML-to-Markdown conversion for common note content.
- Relative Obsidian/GitHub-compatible attachment links.
- Folder-name preservation with a fallback for uncategorized notes.
- Stable filenames based on date and record ID; note bodies are not used in paths.
- Local secret scan that helps prevent sensitive note content from being accidentally uploaded to an open-source repository or GitHub, without printing matching secret values.
- Explicit exclusion of `.obsidian/workspace.json` from Git.
- Python standard library only; no third-party package is required.

## Installation

Copy this directory into your Codex skills directory:

```text
<CODEX_HOME>/skills/oneplus-notes-to-obsidian/
```

The directory must contain:

```text
oneplus-notes-to-obsidian/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── export_coloros_notes.py
```

The skill is automatically discoverable after Codex reloads its skill list. It can also be invoked explicitly as `$oneplus-notes-to-obsidian`.

## Getting a ColorOS Notes Backup

The exact menu names can vary between OnePlus devices and ColorOS versions. A commonly used route is:

1. Open **Settings**, search for **Phone Clone** (`手机搬家`), or open the **Phone Clone** system app.
2. Open the settings gear in the upper-right corner.
3. Choose **Backup and restore** (`备份与恢复`).
4. Choose **Create new backup** (`新建备份`).
5. Open the system-preferences selection and enable **Notes/Labels** (`标签`).
6. Start the backup.

The backup is commonly found at one of these locations:

```text
Internal storage/Android/data/com.oneplus.backuprestore/Backup
External storage/Backup
```

Copy the backup to a computer, then locate the `Data/<backup-id>/Note` directory. The helper expects that directory to contain `rich_note`, `todo`, and `folder`. Attachments are normally inside `files/file_backup.zip`.

For the community reference behind this procedure, see the [original Zhihu answer](https://www.zhihu.com/question/340704022/answer/3428351233) by 阿微Alvin. Menu names and backup paths may differ across device models, regions, and ColorOS releases.

## Usage

Run the helper with paths appropriate for the current machine:

```powershell
python "<skill-root>\scripts\export_coloros_notes.py" `
  --backup-dir "<backup-root>\Data\<backup-id>\Note" `
  --vault-dir "<obsidian-vault>" `
  --backup-id "<backup-id>" `
  --replace
```

`--replace` removes and recreates only the generated export directory inside the vault. Do not use it if that directory contains edits that are not part of the generated backup.

The helper prints a JSON summary. Exit codes:

- `0`: export completed and the secret scan found no matches.
- `1`: invalid input or an export error.
- `2`: export completed, but the secret scan found possible secrets. Do not commit or push until the findings are reviewed.

The `--no-secret-scan` option exists for exceptional local use only. It should not be used before publishing or pushing exported notes.

## Output Layout

By default, the helper writes:

```text
<obsidian-vault>/
└── 手机备份/
    └── 一加备忘录/
        └── <backup-id>/
            ├── 备忘录/
            │   └── <folder>/
            │       └── YYYY-MM-DD-note-<record-id>.md
            ├── 待办/
            │   ├── 待办.md
            │   └── 待办-已删除.md
            ├── 附件/
            └── 导出报告.md
```

The export report contains counts and missing-attachment information. It intentionally does not include secret values.

## GitHub Safety

GitHub upload is a separate, explicit step. The skill must:

1. Use the user's remote URL without embedding credentials.
2. Use the existing Git credential manager or the user's normal authentication flow.
3. Add `.obsidian/workspace.json` to `.gitignore`.
4. Verify that `.obsidian/workspace.json` is neither tracked nor staged.
5. Run the export secret scan before committing.
6. Stop when possible secrets are found.

Never paste API keys, personal access tokens, cookies, or passwords into chat, command arguments, URLs, README files, commit messages, or this skill directory.

## Open-Source Release Checklist

Before publishing changes to this skill:

- Run `quick_validate.py` from the Codex `skill-creator` skill.
- Run `python -m py_compile scripts/export_coloros_notes.py`.
- Search the package for credentials, personal filesystem paths, and unfinished placeholders.
- Review staged filenames as well as file contents; note titles and body excerpts must not become paths.
- Check all external links in the README.
- Keep the included MIT license and contribution/security documents in the release.

## Attribution

The backup-acquisition instructions are based on the community procedure described in the cited Zhihu answer. The exporter itself is designed for local use and does not contact OnePlus, Oppo, Zhihu, GitHub APIs, or any other service automatically.

## Contributing

See [CONTRIBUTING_en.md](.github/CONTRIBUTING_en.md) before opening an issue or pull request. Do not include phone backups, exported notes, API keys, tokens, cookies, or other personal data in contributions.

## License

This project is licensed under the [MIT License](LICENSE).
