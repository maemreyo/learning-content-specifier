# LCS Contract Package

This directory is the source-of-truth metadata for the standalone consumer sync layer.

- `contracts/index.json`: versioned contract index with checksums and compatibility policy.
- `schemas/*.schema.json`: machine contracts consumed by validators and downstream services.
- `docs/contract/*.md`: digest documentation for consumer teams.
- `fixtures/contracts/*.json`: golden fixtures for smoke and integration tests.

The contract package artifact is produced as:

- `.genreleases/lcs-contracts-vX.Y.Z.zip`

Build or verify with:

```bash
uv run python scripts/build_contract_package.py --verify
uv run python scripts/build_contract_package.py --sync --verify --package-version v0.0.0
```

Scaffold a standalone consumer repo with these contract assets pre-synced:

```bash
uv run python scripts/scaffold_output_consumer.py --target ../lcs-output-consumer
```
