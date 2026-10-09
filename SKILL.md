---
name: oneplus-notes-to-obsidian
description: Export OnePlus/Oppo ColorOS Notes backups containing rich_note, todo, folder, and file_backup.zip into an Obsidian vault as Markdown, copy referenced attachments, run a local secret scan, and commit/push to GitHub when explicitly requested.
metadata:
  short-description: Export ColorOS Notes to Obsidian safely
---

# OnePlus Notes To Obsidian

Use this skill when the user wants to extract OnePlus/Oppo/ColorOS Notes or Todo backups into an Obsidian vault, especially from backup folders shaped like `...\Data\<backup-id>\Note` with `rich_note`, `todo`, `folder`, and `files\file_backup.zip`.

If the user has not created a backup yet, use the device-specific acquisition steps in [README.md](README.md) or [README.zh-CN.md](README.zh-CN.md). Menu labels and backup locations can vary by ColorOS version.

## Safety Rules

- Never write, print, or embed API keys, GitHub tokens, cookies, or passwords in the skill files, command lines, commit messages, reports, or chat.
- Do not ask the user to paste a token into chat. Use the machine's existing Git credential manager or ask them to authenticate in their normal Git/GitHub flow.
- Before committing or pushing exported notes, run the export script's secret scan and inspect Git's staged file list. If the scan reports possible secrets, stop before commit/push and report only secret type, file path, and line number; do not show the matching text.
- Keep generated Git paths secret-safe. The helper intentionally uses `date-note-id.md` filenames rather than body excerpts, because note titles or first lines can contain API keys.
- Always exclude `.obsidian/workspace.json` from Git. Add it to `.gitignore` if needed, and verify it is neither tracked nor staged.
- Treat exported notes as private user data. Avoid printing note bodies or file contents unless the user explicitly asks for a specific local file excerpt.

## Export Workflow

1. Locate the ColorOS Note backup directory. It should directly contain `rich_note`, `todo`, and `folder`; attachments are usually in `files\file_backup.zip`.
2. Run the bundled helper:

   ```powershell
   python "<skill-root>\scripts\export_coloros_notes.py" `
     --backup-dir "<backup-root>\Data\<backup-id>\Note" `
     --vault-dir "<obsidian-vault>" `
     --backup-id "<backup-id>" `
     --replace
   ```

   Adjust paths for the current request. Use `--replace` only when overwriting the same generated export directory is intended.

3. Confirm the JSON summary and `导出报告.md`:
   - notes exported equals the `rich_note` count
   - active plus deleted todos equals the `todo` count
   - copied attachments equals the number of attachment records, or any missing matches are explained
   - `secret_findings` is `0` before Git commit/push

4. If GitHub upload is requested:
   - Initialize the vault as a Git repository when needed.
   - Set or verify the remote URL supplied by the user; never include credentials in the URL.
   - Ensure `.gitignore` contains `.obsidian/workspace.json`.
   - Stage the export, desired Obsidian config files, and `.gitignore`.
   - Verify `git diff --cached --name-only -- .obsidian/workspace.json` returns nothing.
   - Commit with a neutral message such as `Import OnePlus ColorOS notes backup`.
   - Push with `git push -u origin main --progress` and wait for a definitive success or failure.

## Helper Script Behavior

`scripts/export_coloros_notes.py` is self-contained and uses only Python standard-library modules. It:

- converts ColorOS `htmlText` into Markdown
- writes one Markdown file per rich note
- writes active and deleted todo summary files
- copies only referenced attachments from `file_backup.zip`
- uses stable non-content filenames to avoid leaking secret-looking text in Git paths
- writes `导出报告.md`
- scans generated text files for common API-key and token patterns without printing matched secret values

When the script exits with code `2`, it completed export but found possible secrets. Do not commit or push until the user resolves or explicitly reviews those local findings.
