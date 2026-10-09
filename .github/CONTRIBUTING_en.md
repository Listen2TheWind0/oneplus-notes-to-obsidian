# Contributing

<div align="center">
  <a href="CONTRIBUTING_en.md"><img src="https://img.shields.io/badge/English-Contribution-11A683?style=for-the-badge" alt="English"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/%E4%B8%AD%E6%96%87-%E8%B4%A1%E7%8C%AE%E6%8C%87%E5%8D%97-59B390?style=for-the-badge" alt="Chinese"></a>
</div>

Thank you for helping improve OnePlus Notes to Obsidian. This project processes phone backups and private notes, so privacy and credential safety come first.

## Before Opening an Issue

Open an issue before starting larger changes, and wait for maintainer feedback before sending a pull request. Please start with an issue for:

- new features, new device or ColorOS compatibility, output-layout changes, or GitHub upload-flow changes;
- uncertain bugs where it is unclear whether the behavior is a parser issue, a backup-format difference, or expected behavior;
- privacy, secret-scanning, filename, attachment-matching, or other data-safety changes.

Do not upload real phone backups, exported notes, attachments, screenshots containing private text, API keys, tokens, cookies, or passwords. Report security and privacy problems privately through [SECURITY.md](SECURITY.md).

## Change Workflow

1. Fork the repository and create a focused branch from `main`, such as `fix/todo-time-parser` or `docs/coloros-backup-path`.
2. Keep one pull request focused on one problem.
3. Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) when practical, such as `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, or `chore:`.
4. Read the [pull request template](PULL_REQUEST_TEMPLATE.md) before opening a pull request.
5. Explain what changed, why it changed, and how it was validated. If a check cannot be completed, explain why.

When user-visible behavior changes, update both `README.md` and `README.zh-CN.md`. If the skill trigger or operating workflow changes, update `SKILL.md` too.

## Project Structure

- **Skill entrypoint**: `SKILL.md` is loaded by Codex. Keep it concise and focused on workflow, safety boundaries, and script entrypoints.
- **Exporter**: `scripts/export_coloros_notes.py` is the core implementation. It uses only the Python standard library and parses `rich_note`, `todo`, `folder`, and `file_backup.zip`.
- **Documentation**: `README.md` and `README.zh-CN.md` must remain consistent.
- **GitHub collaboration files**: `.github/` contains contribution, security, issue, and PR templates.
- **Generated files**: do not commit `__pycache__`, `.pyc`, thumbnail caches, or generated exports.

## Welcome Contributions

- Fix README, `SKILL.md`, help text, broken links, path descriptions, typos, or formatting issues.
- Support additional ColorOS, OxygenOS, or OPPO backup variants with synthetic fixtures or privacy-safe field descriptions.
- Improve HTML-to-Markdown conversion.
- Improve attachment matching, Todo time parsing, folder mapping, or export reports.
- Improve local secret scanning without printing secret values.
- Add tests or validation helpers that do not contain real personal data.

## Contributions We Do Not Want

- Real phone backups, exported notes, photo attachments, or private data.
- API keys, GitHub tokens, cookies, passwords, private keys, or credential-bearing URLs.
- Changes that make the script network by default, upload automatically, push silently, or call external services automatically.
- Removing the `.obsidian/workspace.json` exclusion.
- Reintroducing note titles or body excerpts into generated filenames.
- Large unrelated formatting churn or noisy diffs.

## No Noise-Only Changes

This project does not accept changes whose only purpose is to refresh commit history or create large diffs. These are usually rejected:

- replacing correct wording with equivalent wording;
- changing spaces, blank lines, or wrapping without behavior or rendering impact;
- mechanical replacements that touch unrelated files;
- tiny wording changes without a clear impact.

If a formatting issue affects parsing, rendering, privacy, or user understanding, explain the impact and validation in the pull request.

## Required Validation

Run these commands from the repository root:

```powershell
python "<codex-home>\skills\.system\skill-creator\scripts\quick_validate.py" .
python -c "import py_compile; py_compile.compile('scripts/export_coloros_notes.py', doraise=True)"
```

Also review staged files and diffs for:

- API keys, tokens, cookies, passwords, or credential-bearing URLs;
- personal filesystem paths or private note text;
- real phone backups or generated Obsidian exports;
- `.obsidian/workspace.json`.

The exporter exits with code `2` when it finds possible secrets. Do not bypass this check for pull requests containing exported notes.

## License

By contributing, you agree that your contribution is provided under the [MIT License](../LICENSE).
