# Kế Hoạch Audit + Hardening Full-System cho LCS (Spec-Driven Learning Content, Clean Break)

## Tóm tắt
Mục tiêu là hoàn tất chuyển đổi hệ thống sang workflow phát triển learning content theo `Course → Module → Lesson` với hard gates có thể kiểm chứng, loại bỏ drift giữa template/script/CLI/docs/release package, và chuẩn hóa extension ecosystem theo naming mới.

Bạn đã chốt:
1. Scope: Full system.
2. Hook migration: Clean break.
3. Web benchmark: Targeted official standards.
4. Agent path source-of-truth: `AGENTS.md`.

## Hiện trạng cần xử lý ngay (blocking)
1. `/lcs.charter` đang có thể fail trên branch `main` vì `check-workflow-prereqs` bắt buộc unit-branch (`factory/scripts/bash/check-workflow-prereqs.sh:39`, `factory/templates/commands/charter.md:8`).
2. Release packaging đang rewrite path lỗi thành `.lcs.lcs/...` (`tooling/ci/create-release-packages.sh:33-39`; đã tái hiện trong package output).
3. `factory/templates/vscode-settings.json` và `.devcontainer/devcontainer.json` vẫn gợi ý command cũ (`factory/templates/vscode-settings.json:3-7`, `.devcontainer/devcontainer.json:64-68`).
4. Agent command directories đang lệch chuẩn giữa runtime/docs/release cho `codex`, `kilocode`, `auggie`, `roo` (`tooling/ci/create-release-packages.sh:199-209`, `src/lcs_cli/extensions.py:620-640`, `AGENTS.md`).
5. Extension docs/template còn drift nặng (`speckit_version`, `after_tasks`, `after_implement`) và không khớp validator hiện tại (`extensions/template/extension.yml:33,69,77`; `src/lcs_cli/extensions.py:103-105`).
6. Workflow docs chính vẫn software-first hoặc sai semantic học tập (`README.md`, `spec-driven.md`, `docs/quickstart.md`, `docs/index.md`, `docs/installation.md`, `docs/upgrade.md`).
7. Link docs bị hỏng: `delivery-guide.md` được tham chiếu nhưng file không tồn tại (`docs/index.md:14`, `docs/README.md:30`).
8. Test coverage thiếu cho scripts/release/CLI flows; CI chưa chạy pytest (`tests/` chỉ có `test_extensions.py`, `.github/workflows/lint.yml`).

## Thay đổi public interfaces (breaking) sẽ áp dụng
1. Hook events clean break:
   - Bỏ: `after_tasks`, `after_implement`.
   - Dùng mới: `after_sequence`, `after_author`.
   - Chuẩn mở rộng: `after_<command_verb>` cho toàn bộ core command mới.
2. Extension manifest schema:
   - Bắt buộc `requires.lcs_version`.
   - Loại bỏ `requires.speckit_version`.
3. Agent command layout chuẩn theo `AGENTS.md`:
   - `codex` dùng `.codex/commands/`.
   - `kilocode` dùng `.kilocode/rules/`.
   - `auggie` dùng `.augment/rules/`.
   - `roo` dùng `.roo/rules/`.
4. Script JSON contract chuẩn hóa type + key:
   - `create-new-unit.*`: giữ `UNIT_NAME`, `BRIEF_FILE`, `UNIT_NUM`.
   - `setup-design.*`: giữ `BRIEF_FILE`, `DESIGN_FILE`, `UNIT_DIR`, `BRANCH`, `HAS_GIT` (bool nhất quán 2 shell).
   - `check-workflow-prereqs.*` paths-only: đổi sang key dạng `UNIT_*` (không trả `REPO_ROOT/BRANCH` kiểu cũ).
5. Hard-gate runtime contract cho authoring:
   - `/lcs.audit` chuẩn hóa output report tại `specs/<unit>/audit-report.md`.
   - `/lcs.author` phải chặn tuyệt đối nếu gate chưa pass.

## Kế hoạch triển khai (decision-complete)

## Phase 0 — Contract Freeze và Gap Matrix
1. Tạo baseline matrix trong `docs/system/migration/learning-content-migration-matrix.md` liệt kê từng file drift, mức độ, owner, target fix.
2. Chốt canonical glossary trong `docs/system/migration/terminology.md` (unit, brief, design, sequence, rubric, audit, outputs, charter).
3. Chốt allowlist legacy-term được phép giữ lại chỉ trong changelog/history docs.

**Acceptance:** Có file matrix + glossary; mọi phase sau bám matrix, không quyết định ad-hoc.

## Phase 1 — Rewrite chuẩn cho Workflow Templates
1. Rewrite toàn bộ `factory/templates/commands/*.md` theo skeleton bắt buộc: `Intent`, `Inputs`, `Mandatory Rules (YOU MUST / MUST NOT)`, `Execution Steps`, `Hard Gates`, `Failure Modes`, `Output Contract`, `Examples`.
2. Bổ sung explicit stop conditions cho từng command, đặc biệt `/lcs.author`, `/lcs.audit`, `/lcs.rubric`.
3. Chuẩn hóa handoff chain thành: `charter → define → refine → design → sequence → rubric → audit → author → issueize`.
4. Bổ sung ví dụ success/fail tối thiểu cho mỗi command.

**Acceptance:** Mỗi command file có đủ section chuẩn; không còn command cũ; hard-gate behavior mô tả rõ và kiểm chứng được.

## Phase 2 — Script Layer Hardening (Bash + PowerShell parity)
1. Sửa `check-workflow-prereqs.*` để hỗ trợ `--skip-branch-check` cho `/lcs.charter`.
2. Chuẩn hóa JSON schema paths-only theo naming `UNIT_*`; bỏ keys legacy.
3. Chuẩn hóa bool output type (`HAS_GIT`) đồng nhất giữa bash và powershell.
4. `setup-design.*` chuyển sang create-if-missing để không ghi đè artifact đã có; có flag riêng nếu cần force reset.
5. `common.*` xử lý deterministic hơn khi có nhiều thư mục trùng prefix; fail-fast thay vì warning mơ hồ.
6. `update-agent-context.*` nâng parser metadata robust hơn và đồng bộ vocabulary “unit” thay vì “feature”.

**Acceptance:** Contract JSON của bash/ps đồng nhất; `/lcs.charter` chạy được trên `main`; không còn overwrite ngoài ý muốn.

## Phase 3 — Python Runtime & Extension System Alignment
1. `src/lcs_cli/extensions.py`:
   - Thêm support `codex`.
   - Chuẩn key agent thống nhất với CLI (`cursor-agent` thay vì `cursor`).
   - Validate hook event theo allowlist mới.
2. Đồng bộ toàn bộ extension docs/template:
   - `requires.lcs_version`.
   - Hook events mới.
   - Ví dụ command namespace/hook invocation mới.
3. Update tests trong `tests/` cho manifest schema mới, hook events mới, và agent-path consistency.

**Acceptance:** Extension template tạo ra manifest hợp lệ ngay; test pass cho schema/hook/path mới; không còn drift `speckit_*`.

## Phase 4 — Docs & Diagram Full Sync
1. Rewrite software-first narrative trong `README.md`, `spec-driven.md`, `docs/quickstart.md`, `docs/index.md`, `docs/installation.md`, `docs/upgrade.md` sang learning-content semantics.
2. Sửa toàn bộ link hỏng (`delivery-guide.md` references) và chuẩn hóa TOC/docs routing.
3. Cập nhật `docs/system/codemaps/LCS_Commands/diagram.md` và `docs/system/architect/*.md` theo gate order mới (rubric/audit trước author).
4. Đánh dấu rõ historical context cho tài liệu RFC cũ nếu còn giữ thuật ngữ legacy.

**Acceptance:** Không còn mô tả mâu thuẫn với command/artifact mới; docs build không còn broken links.

## Phase 5 — Release Packaging & Agent Layout Consistency
1. Sửa `create-release-packages.sh`:
   - Bỏ rewrite regex gây `.lcs.lcs`.
   - Đồng bộ đường dẫn agent theo `AGENTS.md`.
2. Sửa `create-github-release.sh` để bảo đảm danh sách assets khớp mapping mới.
3. Kiểm tra smoke package tối thiểu cho `claude`, `codex`, `copilot`, thêm `kilocode`, `auggie`, `roo` vì đang mismatch.
4. Đồng bộ `.devcontainer/devcontainer.json` command recommendations sang command set mới.

**Acceptance:** Package command files không còn path hỏng; folder conventions đúng chuẩn AGENTS cho mọi agent liên quan.

## Phase 6 — Hard-Gate Determinism cho Content Authoring
1. Chuẩn hóa format `rubrics/*.md` để parse machine-friendly (gate id, status, evidence).
2. Chuẩn hóa format `audit-report.md` (severity summary + gate decision PASS/BLOCK).
3. Thêm script gate validator trước `/lcs.author` để chặn runtime nếu unresolved `CRITICAL/HIGH` hoặc rubric còn unchecked.
4. Cập nhật `factory/templates/commands/author.md` để bắt buộc đọc gate validator output thay vì suy luận tự do.

**Acceptance:** `/lcs.author` bị block deterministically khi gate fail, independent với prompt variance.

## Phase 7 — QA Harness + CI Gates
1. Thêm test scripts contract (bash + ps snapshot JSON keys/types).
2. Thêm release packaging smoke test kiểm tra:
   - tên command files mới,
   - đường dẫn `.lcs/*` hợp lệ,
   - không có `.lcs.lcs`.
3. Thêm docs link check.
4. Thêm CI workflow chạy `uv run pytest` + contract smoke; giữ markdownlint hiện có.

**Acceptance:** CI có green path cho test + lint + packaging smoke + docs links.

## Phase 8 — Release Hygiene
1. Update `CHANGELOG.md` entry chi tiết cho breaking interfaces mới.
2. Bump version trong `pyproject.toml` theo semver cho thay đổi breaking.
3. Soạn migration notes riêng cho extension developers (hook event rename + manifest key rename).

**Acceptance:** Release notes đủ để consumer migrate không cần đoán.

## Test cases và kịch bản xác nhận
1. Golden path E2E: `/lcs.define → /lcs.refine → /lcs.design → /lcs.sequence → /lcs.rubric → /lcs.audit → /lcs.author`.
2. Charter on main branch: `/lcs.charter` chạy được khi chưa có unit branch.
3. Hard gate fail path: rubric unchecked hoặc audit còn `CRITICAL/HIGH` thì `/lcs.author` dừng cứng.
4. Script contract parity: bash/ps trả cùng key/type cho từng script.
5. Packaging smoke: `claude`, `codex`, `copilot`, `kilocode`, `auggie`, `roo` đúng folder conventions và command names mới.
6. Extension schema test: manifest mới pass; manifest dùng `speckit_version` fail đúng message.
7. Hook event test: chỉ event mới được chấp nhận; event cũ fail rõ ràng.
8. Docs integrity: không link hỏng; không còn command cũ trong docs hoạt động hiện tại.
9. Legacy token guard: grep fail nếu xuất hiện command/artifact cũ ngoài allowlist lịch sử.

## Assumptions và defaults đã khóa
1. `AGENTS.md` là source-of-truth cho agent folder conventions.
2. Hook events dùng clean break, không alias event cũ.
3. Không giữ backward compatibility cho command/artifact naming cũ.
4. Legacy terms chỉ được phép ở changelog/history context, không ở runtime docs/templates.
5. Áp dụng “local files first”, không thêm LMS publish integration ở repo này.
6. Hard gates phải deterministic bằng script checks, không chỉ dựa prompt text.

## Chuẩn tham chiếu web (dùng để nâng chất workflow)
1. OpenAI Prompt Engineering Guide: cấu trúc instruction rõ role/instructions/examples/context, dùng markdown + XML boundaries, kèm eval loop. https://developers.openai.com/api/docs/guides/prompt-engineering
2. Anthropic Prompting Best Practices: clear/direct/specific, sequential steps, structured XML tags, consistency tag naming. https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/be-clear-and-direct
3. Anthropic XML Tagging: clarity/accuracy/parseability, khuyến nghị tag nhất quán và nested tags. https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags
4. WCAG 2.2: 4 principles (Perceivable, Operable, Understandable, Robust) + conformance levels A/AA/AAA cho accessibility gate. https://www.w3.org/TR/WCAG22/
5. CAST UDL Guidelines 3.0: engagement/representation/action-expression làm nền cho pedagogy consistency gate. https://udlguidelines.cast.org/
6. Constructive Alignment (UNSW): outcomes, activities, assessment phải aligned và vận hành song song để hợp lệ. https://www.teaching.unsw.edu.au/aligning-assessment-learning-outcomes
7. NIH Plain Language: guideline cho readability/clear communication gate. https://www.nih.gov/institutes-nih/nih-office-director/office-communications-public-liaison/clear-communication/plain-language-nih
8. xAPI Spec ecosystem (ADL): nền interoperability/metadata contract cho output artifacts. https://github.com/adlnet/xAPI-Spec
