# Kế Hoạch Tái Tổ Chức Folder Structure: Factory (LCS) → Library (Consumer) → Apps

## 1) Tóm tắt
Bạn **nên** tổ chức lại. Với mô hình bạn nêu (nhà máy sách / thư viện / người đọc), cấu trúc hiện tại đang trộn `factory concerns` và `consumer concerns` trong cùng repo nên dễ drift, khó scale release cadence.

Kế hoạch này đã khóa theo quyết định của bạn:
1. Repo strategy: **Hybrid 2-repo**.
2. Compatibility: **Clean break now**.
3. Execution scope: **Core boundaries first**.
4. Consumer bootstrap mode: **Fetch by release tag**.

## 2) Mục tiêu kiến trúc sau khi tái cấu trúc
1. Repo `learning-content-specifier` chỉ là **Factory Core** (CLI, templates, authoring scripts, release tools, contract publisher).
2. Repo `lcs-output-consumer` là **Library Backbone** độc lập (ingest, validate, catalog/query API).
3. Repo app downstream (learner portal, LMS connector, mobile) chỉ consume qua API/manifest, không phụ thuộc internal path.

## 3) Folder structure mục tiêu (decision-complete)

### 3.1 LCS Core repo (`learning-content-specifier`)
```text
src/lcs_cli/                       # CLI runtime
factory/templates/                 # all command + artifact templates
factory/scripts/bash/              # bash orchestration
factory/scripts/powershell/        # powershell orchestration
factory/scripts/python/            # python validators/build tools
contracts/index.json               # contract package index (giữ entrypoint này)
contracts/schemas/                 # moved from /schemas
contracts/docs/                    # moved from /docs/contract
contracts/fixtures/                # moved from /fixtures/contracts
tooling/ci/                        # moved from .github/workflows/scripts
docs/                              # architecture + guides
tests/                             # all tests
```

### 3.2 Consumer repo (`lcs-output-consumer`)
```text
src/lcs_output_consumer/           # FastAPI + services
contracts/                         # synced contract package from LCS core release
tests/
docs/
```

### 3.3 Apps repos (out-of-scope triển khai, nhưng khóa interface)
```text
<app-repo> -> consume only:
1) Consumer API v1
2) outputs/manifest.json semantics
3) contract version compatibility rules
```

## 4) Public interfaces thay đổi (breaking)
1. **Internal path contract của LCS core đổi hoàn toàn**:
- `templates/*` -> `factory/templates/*`
- `scripts/*` -> `factory/scripts/*`
- `schemas/*` -> `contracts/schemas/*`
- `docs/contract/*` -> `contracts/docs/*`
- `fixtures/contracts/*` -> `contracts/fixtures/*`
- `.github/workflows/scripts/*` -> `tooling/ci/*`

2. **Contract package layout đổi sang namespace thống nhất `contracts/`**:
- Zip mới chứa:
  - `contracts/index.json`
  - `contracts/schemas/*.schema.json`
  - `contracts/docs/*.md`
  - `contracts/fixtures/*.json`

3. **Scaffold consumer embedded bị loại bỏ khỏi core**:
- Bỏ `scaffolds/lcs-output-consumer/`.
- Bỏ script clone local scaffold hiện tại.
- Thay bằng bootstrap script tải template consumer theo release tag.

4. **Bootstrap interface mới**:
- `factory/scripts/python/bootstrap_consumer.py --consumer-version vX.Y.Z --target <path> --contracts-version vA.B.C`
- Cơ chế: fetch release assets + checksum verify + materialize repo.

## 5) Kế hoạch triển khai theo phase

## Phase 0 — Boundary Freeze + Mapping Matrix
1. Tạo `docs/system/restructure/folder-restructure-matrix.md`.
2. Liệt kê toàn bộ old-path -> new-path, owner, test coverage, risk.
3. Freeze naming rules cho 3 domain: `factory`, `contracts`, `tooling`.

**Acceptance**
1. Có matrix đầy đủ cho mọi path đang được CI/release/tests tham chiếu.
2. Không còn quyết định ad-hoc khi move file.

## Phase 1 — Core Folder Move (Clean Break)
1. Move vật lý các thư mục theo target structure.
2. Rewrite toàn bộ path references trong:
- README/docs/architect/codemap
- scripts bash/ps/python
- tests
- release scripts
- workflow YAML
- extension runtime path mappings
3. Chuẩn hóa import/call path trong wrappers bash/ps.
4. Cập nhật legacy-token guard cho đường dẫn mới.

**Acceptance**
1. Không còn reference path cũ trong runtime docs/scripts/tests (trừ changelog/history allowlist).
2. Lint + tests + packaging smoke pass với path mới.

## Phase 2 — Contract Package Rebase
1. Refactor builder để đọc từ `contracts/schemas`, `contracts/docs`, `contracts/fixtures`.
2. Cập nhật `contracts/index.json` entries theo namespace mới.
3. Cập nhật smoke checks và tests tương ứng.

**Acceptance**
1. `build_contract_package --verify` pass.
2. Contract zip chứa đúng tree mới.
3. Consumer checksum verification vẫn deterministic.

## Phase 3 — Consumer Repo Extraction
1. Tạo repo `lcs-output-consumer` độc lập từ scaffold hiện có.
2. Chuyển ownership CI/release của consumer sang repo mới.
3. Trong LCS core, remove scaffold folder và code liên quan embed template.

**Acceptance**
1. Consumer chạy độc lập không cần source tree LCS core.
2. LCS core không còn source code consumer runtime.

## Phase 4 — Bootstrap by Release Tag
1. Thêm bootstrap script mới trong LCS core:
- Download consumer template asset theo tag.
- Verify sha256.
- Download contract package tương ứng.
- Materialize target repo folder.
2. Thêm docs usage + failure modes rõ ràng.

**Acceptance**
1. Bootstrap thành công với tag hợp lệ.
2. Bootstrap fail rõ lỗi với tag thiếu/mismatch checksum/version incompatibility.

## Phase 5 — CI/Release Realignment
1. Update workflow paths sang `tooling/ci/*`.
2. Tách release lanes:
- LCS core release.
- Consumer release.
3. Thêm compatibility check job:
- consumer contract major phải compatible với core contracts major.
4. Thêm drift guard:
- index entries vs files tree vs checksums.

**Acceptance**
1. CI xanh cả Linux/Windows.
2. Release assets đầy đủ và đúng path conventions.
3. Không còn job phụ thuộc path legacy.

## Phase 6 — Docs & Diagram Sync
1. Rewrite architecture docs theo 3-layer model: Factory/Library/Apps.
2. Cập nhật onboarding root README:
- Khi nào dùng core.
- Khi nào dùng consumer.
- Cách bootstrap từ release tags.
3. Update codemap/diagram để phản ánh boundary mới.

**Acceptance**
1. Docs link check = 0 broken links.
2. Narrative nhất quán, không còn nhầm “consumer nằm trong core”.

## 6) Test cases và kịch bản xác nhận
1. `Core regression`: full pytest pass sau move path.
2. `Contract package`: verify + build zip + checksum drift test pass.
3. `Release smoke`: zip assets đúng layout mới `contracts/*`.
4. `Bootstrap success`: tạo repo consumer từ tag hợp lệ và chạy `uv sync`.
5. `Bootstrap fail`: tag không tồn tại / checksum mismatch / incompatible contract major.
6. `Legacy guard`: grep fail nếu còn path cũ ngoài allowlist lịch sử.
7. `Docs integrity`: link check pass sau đổi đường dẫn lớn.
8. `Consumer standalone`: API `/healthz`, `/v1/ingestions/fs`, `/v1/units` hoạt động với contract synced.

## 7) Rủi ro chính và giảm thiểu
1. Rủi ro vỡ CI do clean-break path move.
- Mitigation: matrix-driven rewrite + phase-by-phase smoke.
2. Rủi ro drift giữa core và consumer.
- Mitigation: pin theo release tags + checksum + compatibility job.
3. Rủi ro tăng tải migrate docs/tests.
- Mitigation: codemod theo matrix + legacy token guard.
4. Rủi ro bootstrap network dependency.
- Mitigation: checksum verify + deterministic error taxonomy + local cache fallback.

## 8) Assumptions và defaults đã khóa
1. Không giữ backward alias path cũ.
2. `contracts/index.json` vẫn là entrypoint canonical.
3. Version compatibility theo semver major gate.
4. Consumer bootstrap dùng release assets, không dùng submodule.
5. Apps không triển khai trong batch này, chỉ khóa interface consume.
6. Nếu chạm `src/lcs_cli/__init__.py`, bắt buộc bump `pyproject.toml` và update `CHANGELOG.md`.
