# LCS Contract Package

This directory is the source-of-truth metadata for the standalone consumer sync layer.

- `contracts/index.json`: versioned contract index with checksums and compatibility policy.
- `contracts/schemas/*.schema.json`: machine contracts consumed by validators and downstream services.
- `contracts/docs/*.md`: digest documentation for consumer teams.
- `contracts/fixtures/*.json`: golden fixtures for smoke and integration tests.

The contract package artifact is produced as:

- `.genreleases/lcs-contracts-vX.Y.Z.zip`

Build or verify with:

```bash
uv run python factory/scripts/python/build_contract_package.py --verify
uv run python factory/scripts/python/build_contract_package.py --sync --verify --package-version v0.0.0
```

Scaffold a standalone consumer repo with these contract assets pre-synced:

```bash
uv run python factory/scripts/python/bootstrap_consumer.py --target ../lcs-output-consumer
```
