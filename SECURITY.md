# Security Policy

## Secrets

Never commit API keys, access tokens, passwords, private endpoints, or a populated
`.env` file. Copy `.env.example` to `.env` for local development and keep the
real values only in the local environment or a managed secret store.

If a secret is accidentally committed:

1. Revoke or rotate the secret immediately.
2. Remove it from the current tree.
3. Rewrite the affected Git history before making the repository public.

## Runtime Data

The SQLite database under `data/` and generated reports under `output/` are
local runtime artifacts. They are intentionally excluded from version control.

## Reporting

Please do not disclose a suspected vulnerability in a public issue. Contact the
repository owner privately with reproduction steps and the affected component.

