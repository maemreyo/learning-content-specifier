# Kế Hoạch Triển Khai Chi Tiết: LCS Flow Improvements (Greenfield, Decision-Complete)

## Tóm tắt
Mục tiêu là triển khai proposal thành hệ thống authoring learning content deterministic, hard-gated, machine-consumable, theo chuỗi command giữ nguyên:
`/lcs.charter -> /lcs.define -> /lcs.refine -> /lcs.design -> /lcs.sequence -> /lcs.rubric -> /lcs.audit -> /lcs.author -> /lcs.issueize`.

Plan này khóa toàn bộ quyết định còn mở:
1. Pedagogy profile mặc định v1: `Corporate L&D`.
2. Interop v1: `xAPI required`, CASE/QTI/LTI/cmi5 là optional adapters.
3. Chiến lược thực thi: `vertical slices` (mỗi slice chạy end-to-end và có test).

## Quyết định đã khóa (implementation defaults)
1. Trọng số pedagogy scoring (Corporate L&D):
   - `outcome_fit=0.30`
   - `evidence_fit=0.25`
   - `learner_fit=0.20`
   - `delivery_fit=0.15`
   - `accessibility_fit=0.10`
2. Thang điểm từng dimension: `0..5`; điểm tổng chuẩn hóa về `0..1`.
3. Rule chọn phương pháp:
   - Chọn `1 primary method` có score cao nhất.
   - Chọn tối đa `2 secondary methods` nếu `score_delta <= 0.40` (trên thang 0..5 trước chuẩn hóa).
4. Ngưỡng confidence để bắt buộc web research: `confidence < 0.70`.
5. Duration tolerance gate cho content-model: `-10%` đến `+15%` so với budget từ `brief.md`.
6. Author hard-stop: block nếu còn bất kỳ `CRITICAL|HIGH` unresolved hoặc rubric có status non-pass/unchecked.
7. Interop policy v1:
   - Bắt buộc: `xAPI` block trong manifest.
   - Optional: `case`, `qti`, `lti`, `cmi5`.

## Public interfaces / contracts sẽ áp dụng
1. Artifact contract v1 (machine-readable bắt buộc):
   - `specs/<unit>/brief.json`
   - `specs/<unit>/design.json`
   - `specs/<unit>/sequence.json`
   - `specs/<unit>/audit-report.json`
   - `specs/<unit>/outputs/manifest.json`
2. Manifest-first consumption:
   - Consumer chỉ đọc `specs/<unit>/outputs/manifest.json` làm entrypoint.
   - Cấm path-guessing ngoài manifest.
3. Schema strategy:
   - JSON Schema 2020-12.
   - `$id` dạng `lcs.artifact.<type>.v1`.
   - Semver contract: major=breaking, minor=additive, patch=non-structural fix.
4. Runtime gate contract:
   - `audit-report.md` vẫn giữ để human-readable.
   - `audit-report.json` là machine contract tương đương.
   - `/lcs.author` phải parse validator output thay vì suy luận tự do.

## Kế hoạch triển khai theo Vertical Slices

## Slice 1 — Artifact JSON Contract Foundation (end-to-end)
1. Thêm schema files:
   - `contracts/schemas/brief.schema.json`
   - `contracts/schemas/design.schema.json`
   - `contracts/schemas/sequence.schema.json`
   - `contracts/schemas/audit-report.schema.json`
   - `contracts/schemas/manifest.schema.json`
2. Thêm script validator dùng chung:
   - `factory/scripts/bash/validate-artifact-contracts.sh`
   - `factory/scripts/powershell/validate-artifact-contracts.ps1`
3. Cập nhật template contracts:
   - `factory/templates/commands/design.md`
   - `factory/templates/commands/sequence.md`
   - `factory/templates/commands/audit.md`
   - `factory/templates/commands/author.md`
   - `factory/templates/sequence-template.md` đổi `package-manifest.json` -> `manifest.json`.
4. Cập nhật script orchestration để đảm bảo create-if-missing file JSON bên cạnh markdown:
   - `factory/scripts/bash/setup-design.sh`
   - `factory/scripts/powershell/setup-design.ps1`
5. Acceptance của slice:
   - Tạo unit mẫu có đủ 5 JSON bắt buộc.
   - `validate-artifact-contracts` pass với schema.
   - Không phá chuỗi command hiện hữu.

## Slice 2 — Decision Engine (Content Model + Pedagogy + Research Policy)
1. Chuẩn hóa decision object trong `design`:
   - Output thêm `specs/<unit>/design-decisions.json`.
   - Bắt buộc fields: `candidate_methods[]`, `scores`, `selected_primary`, `selected_secondary[]`, `rationale`, `confidence`.
2. Chuẩn hóa content model machine contract:
   - `specs/<unit>/content-model.json` gồm `course/modules/lessons` + `lo_refs`.
   - Thêm dependency graph + cycle-check result.
3. Web-research trigger policy thực thi ở `design` và `audit`:
   - Trigger khi time-sensitive, confidence thấp, conflict artifacts, user yêu cầu.
   - Persist evidence vào `specs/<unit>/research.md` + references trong `design-decisions.json`.
4. Cập nhật command docs để deterministic:
   - `factory/templates/commands/design.md`
   - `factory/templates/commands/audit.md`
5. Acceptance của slice:
   - Có scoring log đầy đủ.
   - Có lý do chọn pedagogy có thể audit lại.
   - Web research trigger hoạt động đúng theo policy đã khóa.

## Slice 3 — Hard Gate Determinism for Author
1. Cứng hóa rubric parsing format:
   - Giữ format gate line trong `factory/templates/rubric-template.md`.
   - Ràng buộc parser dùng regex ổn định, không phụ thuộc văn phong.
2. Đồng bộ validator bash/ps:
   - `factory/scripts/bash/validate-author-gates.sh`
   - `factory/scripts/powershell/validate-author-gates.ps1`
   - Bắt buộc đọc cả `audit-report.md` và `audit-report.json` (json là source ưu tiên nếu có).
3. Cập nhật author command contract:
   - `factory/templates/commands/author.md` chỉ cho author khi `STATUS=PASS`.
4. Cập nhật audit command contract:
   - `factory/templates/commands/audit.md` bắt buộc xuất đồng thời markdown + json.
5. Acceptance của slice:
   - Fail path deterministic giữa bash/ps.
   - `/lcs.author` luôn block khi gate fail, không phụ thuộc prompt variance.

## Slice 4 — Packaging + Agent Consistency
1. Kiểm tra và harden packaging script:
   - `tooling/ci/create-release-packages.sh`
   - đảm bảo không sinh đường dẫn lỗi kiểu `.lcs.lcs`.
   - map agent folder đúng `AGENTS.md`.
2. Đồng bộ GitHub release assets:
   - `tooling/ci/create-github-release.sh`
3. Đồng bộ extension/runtime agent mapping:
   - `src/lcs_cli/__init__.py`
   - `src/lcs_cli/extensions.py`
4. Acceptance của slice:
   - Smoke package pass cho `claude`, `codex`, `copilot`, `kilocode`, `auggie`, `roo`.
   - Command files trong package dùng naming mới và path đúng.

## Slice 5 — Docs + Diagram Sync
1. Đồng bộ proposal thành docs runtime:
   - `docs/system/codemaps/LCS_Commands/diagram.md`
   - `docs/system/architect/spec-driven-workflow.md`
   - `README.md`
   - `spec-driven.md`
2. Chuẩn hóa docs command contracts theo “YOU MUST / MUST NOT” + failure modes + examples:
   - `factory/templates/commands/*.md` đã có khung, bổ sung các phần còn thiếu deterministic details.
3. Sửa link integrity và naming consistency:
   - đảm bảo không còn tham chiếu artifact cũ.
4. Acceptance của slice:
   - Link check pass.
   - Narrative nhất quán learning-content-first toàn bộ docs chính.

## Slice 6 — QA Harness + CI Gates + Release Hygiene
1. Mở rộng test suite:
   - `tests/test_artifact_contracts.py` cho schema validation.
   - `tests/test_gate_determinism.py` cho author block conditions.
   - `tests/test_pedagogy_decisions.py` cho scoring + selection rules.
2. Mở rộng smoke scripts nếu cần:
   - `tooling/ci/test-script-contracts.sh`
   - `tooling/ci/test-script-contracts.ps1`
   - `tooling/ci/smoke-release-packages.sh`
3. CI workflow:
   - giữ `uv run pytest -q`.
   - giữ docs link check + legacy token guard.
4. Release hygiene:
   - `CHANGELOG.md` ghi rõ breaking interfaces mới.
   - `pyproject.toml` bump major/minor theo semver thực tế release.
5. Acceptance của slice:
   - CI xanh trên Linux + Windows contract checks.
   - Release notes đủ để consumer và extension devs migrate không đoán.

## Test cases và kịch bản xác nhận
1. Golden path E2E:
   - `/lcs.define -> /lcs.refine -> /lcs.design -> /lcs.sequence -> /lcs.rubric -> /lcs.audit -> /lcs.author`.
   - Kỳ vọng có đầy đủ markdown + JSON artifacts; author thành công khi gates pass.
2. Hard gate fail:
   - Tạo rubric unchecked hoặc audit có HIGH.
   - `/lcs.author` trả BLOCK deterministic ở cả bash và ps.
3. Content model determinism:
   - Input brief giống nhau phải sinh structure LO mapping nhất quán.
   - Fail nếu dependency graph cyclic.
4. Pedagogy decision determinism:
   - Cùng input profile Corporate L&D cho cùng output `selected_primary` và score.
   - Trigger web research khi confidence < 0.70.
5. Manifest contract:
   - Consumer test chỉ đọc `outputs/manifest.json`.
   - Fail nếu thiếu `contract_version`, `artifacts[]`, `xapi`.
6. Packaging smoke:
   - Verify path conventions theo `AGENTS.md`.
   - Không tồn tại `.lcs.lcs`.
7. Docs integrity:
   - Broken links = 0.
   - Không còn command/artifact legacy ngoài allowlist history/changelog.

## Rủi ro chính và cách giảm thiểu
1. Drift giữa markdown và json artifacts.
   - Mitigation: schema validator bắt buộc trong CI + contract tests.
2. Heuristic parser không ổn định giữa shell.
   - Mitigation: ưu tiên json contract parse, markdown chỉ để human-read.
3. Web research gây non-deterministic output.
   - Mitigation: trigger policy rõ ràng + bắt buộc lưu evidence + source references.
4. Tăng độ phức tạp cho creators.
   - Mitigation: giữ command surface đơn giản, complexity nằm ở orchestration nội bộ.

## Assumptions và phạm vi
1. Greenfield hoàn toàn, không làm migration/backward compatibility cho naming cũ.
2. Không thêm LMS publish integration trực tiếp ở repo này.
3. Local-files-first là nguyên tắc bắt buộc.
4. `AGENTS.md` là source-of-truth cho agent folders/conventions.
5. Các chuẩn web dùng làm benchmark chất lượng, không ép full compliance ngay ở v1 trừ những contract đã khóa ở trên.
