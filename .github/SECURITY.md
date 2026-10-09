# Security and Privacy

This project processes private phone-backup data locally. Please treat exported notes and attachments as sensitive personal data.

## Do Not Publish

Never publish or attach:

- API keys, GitHub tokens, cookies, passwords, or credential files;
- ColorOS backup directories;
- exported Markdown notes or private attachments;
- screenshots or logs containing personal note content;
- remote URLs containing embedded credentials.

The repository's exporter includes a local secret scan, but no automated scanner is complete. Review both file contents and filenames before committing.

## Reporting a Problem

For a security or privacy issue, do not open a public issue with sensitive details. Use GitHub's private vulnerability-reporting mechanism for the repository when available, or contact the repository maintainer privately through GitHub.

When reporting, provide the smallest reproducible description possible. Redact secret values and personal data. A pattern description, affected file, and safe reproduction steps are usually enough.

## If a Secret Was Exposed

1. Revoke or rotate the credential immediately.
2. Remove the secret from the working tree.
3. Check Git history and remote copies.
4. Report the incident privately.

Removing a secret from the latest commit does not remove it from Git history. History rewriting and remote cleanup may be required.
