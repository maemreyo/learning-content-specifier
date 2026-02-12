#!/usr/bin/env python3
"""Scaffold a standalone tutoring-platform monorepo for Teacher Studio + Learner Portal."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import textwrap
from pathlib import Path


SEMVER_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
DEFAULT_CONTRACT_VERSION_FILE = (
    Path(__file__).resolve().parents[3] / "contracts" / "consumer-contract-version.txt"
)


class ScaffoldError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="Target directory for the tutoring-platform repository")
    parser.add_argument(
        "--consumer-base-url",
        default="http://localhost:8000",
        help="Base URL for lcs-output-consumer API",
    )
    parser.add_argument(
        "--contracts-version",
        help="Pinned required contract version (X.Y.Z). Fallback reads contracts/consumer-contract-version.txt",
    )
    parser.add_argument(
        "--contracts-version-file",
        default=str(DEFAULT_CONTRACT_VERSION_FILE),
        help="Fallback file for required contract version when --contracts-version is omitted",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite non-empty target directory")
    return parser.parse_args()


def resolve_contract_version(explicit_value: str | None, fallback_file: str | None) -> str:
    candidate = (explicit_value or "").strip()
    if not candidate and fallback_file:
        path = Path(fallback_file).expanduser().resolve()
        if path.is_file():
            candidate = path.read_text(encoding="utf-8").strip()

    if not candidate:
        raise ScaffoldError(
            "Missing contracts version. Provide --contracts-version or maintain contracts/consumer-contract-version.txt."
        )

    if not SEMVER_VERSION_PATTERN.match(candidate):
        raise ScaffoldError(f"Invalid contracts version '{candidate}', expected X.Y.Z")

    return candidate


def prepare_target(target: Path, force: bool) -> None:
    if target.exists() and any(target.iterdir()):
        if not force:
            raise ScaffoldError(f"Target directory is not empty: {target} (use --force)")
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)


def write_file(base_dir: Path, relative_path: str, content: str) -> None:
    path = base_dir / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_files(consumer_base_url: str, contracts_version: str) -> dict[str, str]:
    root_package = {
        "name": "tutoring-platform",
        "private": True,
        "version": "0.1.0",
        "packageManager": "pnpm@10.0.0",
        "scripts": {
            "build": "turbo run build",
            "dev": "turbo run dev --parallel",
            "lint": "turbo run lint",
            "test": "turbo run test",
            "typecheck": "turbo run typecheck",
        },
        "devDependencies": {
            "turbo": "^2.0.0",
            "typescript": "^5.6.0",
        },
    }

    files: dict[str, str] = {
        ".gitignore": textwrap.dedent(
            """\
            node_modules
            .turbo
            .next
            dist
            .env
            .env.local
            .DS_Store
            """
        ),
        "package.json": json.dumps(root_package, indent=2) + "\n",
        "pnpm-workspace.yaml": textwrap.dedent(
            """\
            packages:
              - "apps/*"
              - "services/*"
              - "packages/*"
            """
        ),
        "turbo.json": textwrap.dedent(
            """\
            {
              "$schema": "https://turbo.build/schema.json",
              "tasks": {
                "build": {
                  "dependsOn": ["^build"],
                  "outputs": ["dist/**", ".next/**"]
                },
                "dev": {
                  "cache": false,
                  "persistent": true
                },
                "lint": {
                  "dependsOn": ["^lint"]
                },
                "test": {
                  "dependsOn": ["^test"]
                },
                "typecheck": {
                  "dependsOn": ["^typecheck"]
                }
              }
            }
            """
        ),
        "tsconfig.base.json": textwrap.dedent(
            """\
            {
              "compilerOptions": {
                "target": "ES2022",
                "module": "ESNext",
                "moduleResolution": "Bundler",
                "strict": true,
                "esModuleInterop": true,
                "skipLibCheck": true,
                "forceConsistentCasingInFileNames": true,
                "declaration": true,
                "declarationMap": true
              }
            }
            """
        ),
        ".env.example": textwrap.dedent(
            f"""\
            CONSUMER_BASE_URL={consumer_base_url}
            REQUIRED_CONTRACT_VERSION={contracts_version}
            SUPABASE_URL=
            SUPABASE_ANON_KEY=
            SUPABASE_SERVICE_ROLE_KEY=
            """
        ),
        "contracts/consumer-contract-version.txt": f"{contracts_version}\n",
        "integration-manifest.md": textwrap.dedent(
            f"""\
            # Tutoring Platform Integration Manifest (v1)

            ## Topology
            - `learning-content-specifier` (Factory): produces contracts/artifacts.
            - `lcs-output-consumer` (Library): validates and exposes unit catalog.
            - `tutoring-platform` (Apps): teacher + learner applications.

            ## Access Policy
            - Frontends (`apps/teacher`, `apps/learner`) MUST call BFF only.
            - BFF is the only component allowed to call consumer APIs.

            ## Consumer API Dependency
            - Base URL: `{consumer_base_url}`
            - Required endpoints:
              - `GET /v1/units`
              - `GET /v1/units/{{unit_id}}`
              - `GET /v1/units/{{unit_id}}/manifest`
              - `GET /v1/units/{{unit_id}}/gates`

            ## BFF Public API (v1)
            - `GET /api/v1/catalog/units`
            - `GET /api/v1/catalog/units/{{unit_id}}`
            - `POST /api/v1/assignments`
            - `GET /api/v1/assignments`
            - `GET /api/v1/assignments/{{assignment_id}}`
            - `POST /api/v1/submissions`
            - `GET /api/v1/students/{{student_id}}/progress`
            - `POST /api/v1/grades`
            - `GET /api/v1/analytics/classrooms/{{classroom_id}}`
            - `POST /api/v1/events/xapi`

            ## Compatibility Rule
            - Required contract version pin: `{contracts_version}`
            - Runtime MUST block if consumer package major version does not match this pin.
            """
        ),
        "README.md": textwrap.dedent(
            """\
            # Tutoring Platform

            Teacher Studio + Learner Portal monorepo for LCS-based tutoring workflow.

            ## Workspace
            - `apps/teacher`: assignment, grading, analytics UI.
            - `apps/learner`: assignment execution and submission UI.
            - `services/bff`: API gateway and domain logic.
            - `services/workers`: async event aggregation workers.
            - `packages/api-client`: typed API clients for frontends.
            - `packages/types`: shared domain types.
            - `packages/shared-ui`: reusable UI components.
            - `infra/supabase`: schema, RLS, seed.

            ## Quick Start
            1. `cp .env.example .env`
            2. `pnpm install`
            3. `pnpm dev`

            ## Rule
            Frontend apps MUST call BFF only. No direct calls to `lcs-output-consumer`.
            """
        ),
        ".github/workflows/ci.yml": textwrap.dedent(
            """\
            name: CI

            on:
              push:
                branches: ["main"]
              pull_request:

            jobs:
              build:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v4
                  - uses: actions/setup-node@v4
                    with:
                      node-version: "20"
                  - uses: pnpm/action-setup@v4
                    with:
                      version: 10
                  - run: pnpm install --frozen-lockfile=false
                  - run: pnpm turbo run typecheck
                  - run: pnpm turbo run build
            """
        ),
        "apps/teacher/package.json": textwrap.dedent(
            """\
            {
              "name": "@tutoring/teacher",
              "private": true,
              "version": "0.1.0",
              "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "typecheck": "tsc --noEmit"
              },
              "dependencies": {
                "next": "15.0.0",
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
                "@tutoring/api-client": "workspace:*",
                "@tutoring/types": "workspace:*"
              },
              "devDependencies": {
                "@types/node": "^22.10.0",
                "@types/react": "^18.3.0",
                "@types/react-dom": "^18.3.0",
                "typescript": "^5.6.0"
              }
            }
            """
        ),
        "apps/teacher/tsconfig.json": textwrap.dedent(
            """\
            {
              "extends": "../../tsconfig.base.json",
              "compilerOptions": {
                "jsx": "preserve",
                "lib": ["dom", "dom.iterable", "esnext"]
              },
              "include": ["**/*.ts", "**/*.tsx"]
            }
            """
        ),
        "apps/teacher/next.config.mjs": "export default {};\n",
        "apps/teacher/app/layout.tsx": textwrap.dedent(
            """\
            export default function RootLayout({ children }: { children: React.ReactNode }) {
              return (
                <html lang="en">
                  <body>{children}</body>
                </html>
              );
            }
            """
        ),
        "apps/teacher/app/page.tsx": textwrap.dedent(
            """\
            export default function TeacherHome() {
              return (
                <main>
                  <h1>Teacher Studio</h1>
                  <p>Assignments, grading, and analytics are managed via BFF APIs.</p>
                </main>
              );
            }
            """
        ),
        "apps/learner/package.json": textwrap.dedent(
            """\
            {
              "name": "@tutoring/learner",
              "private": true,
              "version": "0.1.0",
              "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "typecheck": "tsc --noEmit"
              },
              "dependencies": {
                "next": "15.0.0",
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
                "@tutoring/api-client": "workspace:*",
                "@tutoring/types": "workspace:*"
              },
              "devDependencies": {
                "@types/node": "^22.10.0",
                "@types/react": "^18.3.0",
                "@types/react-dom": "^18.3.0",
                "typescript": "^5.6.0"
              }
            }
            """
        ),
        "apps/learner/tsconfig.json": textwrap.dedent(
            """\
            {
              "extends": "../../tsconfig.base.json",
              "compilerOptions": {
                "jsx": "preserve",
                "lib": ["dom", "dom.iterable", "esnext"]
              },
              "include": ["**/*.ts", "**/*.tsx"]
            }
            """
        ),
        "apps/learner/next.config.mjs": "export default {};\n",
        "apps/learner/app/layout.tsx": textwrap.dedent(
            """\
            export default function RootLayout({ children }: { children: React.ReactNode }) {
              return (
                <html lang="en">
                  <body>{children}</body>
                </html>
              );
            }
            """
        ),
        "apps/learner/app/page.tsx": textwrap.dedent(
            """\
            export default function LearnerHome() {
              return (
                <main>
                  <h1>Learner Portal</h1>
                  <p>Assignments and feedback are consumed from tutoring BFF endpoints.</p>
                </main>
              );
            }
            """
        ),
        "services/bff/package.json": textwrap.dedent(
            """\
            {
              "name": "@tutoring/bff",
              "private": true,
              "version": "0.1.0",
              "type": "module",
              "scripts": {
                "dev": "tsx watch src/index.ts",
                "build": "tsc -p tsconfig.json",
                "start": "node dist/index.js",
                "typecheck": "tsc --noEmit"
              },
              "dependencies": {
                "fastify": "^5.1.0",
                "@tutoring/types": "workspace:*"
              },
              "devDependencies": {
                "tsx": "^4.19.2",
                "typescript": "^5.6.0"
              }
            }
            """
        ),
        "services/bff/tsconfig.json": textwrap.dedent(
            """\
            {
              "extends": "../../tsconfig.base.json",
              "compilerOptions": {
                "outDir": "dist",
                "rootDir": "src"
              },
              "include": ["src/**/*.ts"]
            }
            """
        ),
        "services/bff/src/consumer-client.ts": textwrap.dedent(
            """\
            export class ConsumerClient {
              constructor(private readonly baseUrl: string) {}

              async getUnits(): Promise<unknown> {
                const response = await fetch(`${this.baseUrl}/v1/units`);
                if (!response.ok) throw new Error(`Consumer getUnits failed: ${response.status}`);
                return response.json();
              }

              async getUnit(unitId: string): Promise<unknown> {
                const response = await fetch(`${this.baseUrl}/v1/units/${unitId}`);
                if (!response.ok) throw new Error(`Consumer getUnit failed: ${response.status}`);
                return response.json();
              }
            }
            """
        ),
        "services/bff/src/index.ts": textwrap.dedent(
            """\
            import Fastify from "fastify";
            import { ConsumerClient } from "./consumer-client.js";

            const app = Fastify({ logger: true });
            const consumer = new ConsumerClient(process.env.CONSUMER_BASE_URL || "http://localhost:8000");

            app.get("/healthz", async () => ({ status: "ok" }));

            app.get("/api/v1/catalog/units", async () => consumer.getUnits());
            app.get("/api/v1/catalog/units/:unitId", async (request) => {
              const params = request.params as { unitId: string };
              return consumer.getUnit(params.unitId);
            });

            app.post("/api/v1/events/xapi", async (request) => {
              const payload = request.body as Record<string, unknown>;
              return { accepted: true, event: payload };
            });

            app.post("/api/v1/assignments", async () => ({ created: true }));
            app.get("/api/v1/assignments", async () => ({ items: [] }));
            app.get("/api/v1/assignments/:assignmentId", async () => ({ item: null }));
            app.post("/api/v1/submissions", async () => ({ created: true }));
            app.get("/api/v1/students/:studentId/progress", async () => ({ progress: [] }));
            app.post("/api/v1/grades", async () => ({ graded: true }));
            app.get("/api/v1/analytics/classrooms/:classroomId", async () => ({ metrics: {} }));

            const port = Number(process.env.PORT || "8080");
            app.listen({ host: "0.0.0.0", port }).catch((error) => {
              app.log.error(error);
              process.exit(1);
            });
            """
        ),
        "services/workers/package.json": textwrap.dedent(
            """\
            {
              "name": "@tutoring/workers",
              "private": true,
              "version": "0.1.0",
              "type": "module",
              "scripts": {
                "dev": "tsx watch src/index.ts",
                "build": "tsc -p tsconfig.json",
                "start": "node dist/index.js",
                "typecheck": "tsc --noEmit"
              },
              "dependencies": {
                "@tutoring/types": "workspace:*"
              },
              "devDependencies": {
                "tsx": "^4.19.2",
                "typescript": "^5.6.0"
              }
            }
            """
        ),
        "services/workers/tsconfig.json": textwrap.dedent(
            """\
            {
              "extends": "../../tsconfig.base.json",
              "compilerOptions": {
                "outDir": "dist",
                "rootDir": "src"
              },
              "include": ["src/**/*.ts"]
            }
            """
        ),
        "services/workers/src/index.ts": textwrap.dedent(
            """\
            type XapiEvent = {
              event_id: string;
              assignment_id: string;
              student_id: string;
              lo_id: string;
              score?: number;
              timestamp: string;
            };

            export function aggregateEvent(event: XapiEvent) {
              return {
                key: `${event.assignment_id}:${event.student_id}:${event.lo_id}`,
                score: event.score ?? 0,
                timestamp: event.timestamp,
              };
            }

            console.log("worker started");
            """
        ),
        "packages/types/package.json": textwrap.dedent(
            """\
            {
              "name": "@tutoring/types",
              "private": true,
              "version": "0.1.0",
              "type": "module",
              "main": "src/index.ts",
              "scripts": {
                "build": "tsc -p tsconfig.json",
                "typecheck": "tsc --noEmit"
              },
              "devDependencies": {
                "typescript": "^5.6.0"
              }
            }
            """
        ),
        "packages/types/tsconfig.json": textwrap.dedent(
            """\
            {
              "extends": "../../tsconfig.base.json",
              "compilerOptions": {
                "outDir": "dist",
                "rootDir": "src"
              },
              "include": ["src/**/*.ts"]
            }
            """
        ),
        "packages/types/src/index.ts": textwrap.dedent(
            """\
            export type AssignmentStatus = "draft" | "active" | "closed";

            export interface Assignment {
              id: string;
              teacher_id: string;
              unit_id: string;
              unit_title: string;
              unit_version: string;
              outcomes_snapshot: Array<{ lo_id: string; priority: string }>;
              student_ids: string[];
              due_date: string;
              status: AssignmentStatus;
              instructions: string;
            }

            export interface OutcomeProgress {
              lo_id: string;
              mastered: boolean;
              score?: number;
              attempts: number;
            }

            export interface StudentProgress {
              assignment_id: string;
              student_id: string;
              unit_id: string;
              started_at: string;
              completed_at?: string;
              time_spent_seconds: number;
              outcomes_completed: OutcomeProgress[];
              completion_rate: number;
              mastery_score?: number;
            }
            """
        ),
        "packages/api-client/package.json": textwrap.dedent(
            """\
            {
              "name": "@tutoring/api-client",
              "private": true,
              "version": "0.1.0",
              "type": "module",
              "main": "src/index.ts",
              "scripts": {
                "build": "tsc -p tsconfig.json",
                "typecheck": "tsc --noEmit"
              },
              "dependencies": {
                "@tutoring/types": "workspace:*"
              },
              "devDependencies": {
                "typescript": "^5.6.0"
              }
            }
            """
        ),
        "packages/api-client/tsconfig.json": textwrap.dedent(
            """\
            {
              "extends": "../../tsconfig.base.json",
              "compilerOptions": {
                "outDir": "dist",
                "rootDir": "src"
              },
              "include": ["src/**/*.ts"]
            }
            """
        ),
        "packages/api-client/src/index.ts": textwrap.dedent(
            """\
            export class BffClient {
              constructor(private readonly baseUrl: string) {}

              async getCatalogUnits() {
                return this.getJson("/api/v1/catalog/units");
              }

              async getCatalogUnit(unitId: string) {
                return this.getJson(`/api/v1/catalog/units/${unitId}`);
              }

              async createAssignment(payload: Record<string, unknown>) {
                return this.postJson("/api/v1/assignments", payload);
              }

              private async getJson(path: string) {
                const response = await fetch(`${this.baseUrl}${path}`);
                if (!response.ok) throw new Error(`BFF GET failed: ${response.status}`);
                return response.json();
              }

              private async postJson(path: string, payload: Record<string, unknown>) {
                const response = await fetch(`${this.baseUrl}${path}`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(payload),
                });
                if (!response.ok) throw new Error(`BFF POST failed: ${response.status}`);
                return response.json();
              }
            }
            """
        ),
        "packages/shared-ui/package.json": textwrap.dedent(
            """\
            {
              "name": "@tutoring/shared-ui",
              "private": true,
              "version": "0.1.0",
              "type": "module",
              "main": "src/index.tsx",
              "scripts": {
                "build": "tsc -p tsconfig.json",
                "typecheck": "tsc --noEmit"
              },
              "dependencies": {
                "react": "^18.3.1"
              },
              "devDependencies": {
                "@types/react": "^18.3.0",
                "typescript": "^5.6.0"
              }
            }
            """
        ),
        "packages/shared-ui/tsconfig.json": textwrap.dedent(
            """\
            {
              "extends": "../../tsconfig.base.json",
              "compilerOptions": {
                "outDir": "dist",
                "rootDir": "src",
                "jsx": "react-jsx"
              },
              "include": ["src/**/*.tsx"]
            }
            """
        ),
        "packages/shared-ui/src/index.tsx": textwrap.dedent(
            """\
            import React from "react";

            export function StatusBadge({ label }: { label: string }) {
              return <span style={{ padding: "4px 8px", border: "1px solid #999" }}>{label}</span>;
            }
            """
        ),
        "infra/supabase/README.md": textwrap.dedent(
            """\
            # Supabase Infra

            This folder holds schema migrations, RLS policies, and seed data for tutoring-platform.

            Apply migrations with your preferred Supabase CLI workflow.
            """
        ),
        "infra/supabase/migrations/0001_init.sql": textwrap.dedent(
            """\
            -- Core domain tables for teacher + learner workflow.
            create table if not exists users (
              id uuid primary key,
              role text not null check (role in ('teacher', 'student', 'admin')),
              display_name text not null
            );

            create table if not exists classrooms (
              id uuid primary key,
              teacher_id uuid not null references users(id),
              name text not null
            );

            create table if not exists enrollments (
              classroom_id uuid not null references classrooms(id),
              student_id uuid not null references users(id),
              primary key (classroom_id, student_id)
            );

            create table if not exists assignments (
              id uuid primary key,
              classroom_id uuid not null references classrooms(id),
              teacher_id uuid not null references users(id),
              unit_id text not null,
              unit_title text not null,
              unit_version text not null,
              outcomes_snapshot jsonb not null,
              manifest_ref text not null,
              due_at timestamptz not null,
              status text not null check (status in ('draft', 'active', 'closed'))
            );

            create table if not exists assignment_targets (
              assignment_id uuid not null references assignments(id),
              student_id uuid not null references users(id),
              primary key (assignment_id, student_id)
            );

            create table if not exists submissions (
              id uuid primary key,
              assignment_id uuid not null references assignments(id),
              student_id uuid not null references users(id),
              submitted_at timestamptz not null default now(),
              payload jsonb not null
            );

            create table if not exists event_inbox (
              event_id text primary key,
              assignment_id uuid not null references assignments(id),
              student_id uuid not null references users(id),
              lo_id text not null,
              payload jsonb not null,
              received_at timestamptz not null default now()
            );

            create table if not exists outcome_progress (
              assignment_id uuid not null references assignments(id),
              student_id uuid not null references users(id),
              lo_id text not null,
              attempts int not null default 0,
              latest_score numeric,
              mastered boolean not null default false,
              updated_at timestamptz not null default now(),
              primary key (assignment_id, student_id, lo_id)
            );

            create table if not exists progress_snapshots (
              assignment_id uuid not null references assignments(id),
              student_id uuid not null references users(id),
              completion_rate numeric not null default 0,
              mastery_score numeric,
              updated_at timestamptz not null default now(),
              primary key (assignment_id, student_id)
            );

            create table if not exists grades (
              id uuid primary key,
              assignment_id uuid not null references assignments(id),
              student_id uuid not null references users(id),
              teacher_id uuid not null references users(id),
              final_grade numeric not null,
              outcome_grades jsonb not null,
              overall_feedback text,
              graded_at timestamptz not null default now()
            );

            -- RLS TODO: add teacher/student policies in follow-up migration.
            """
        ),
        "infra/supabase/seed.sql": textwrap.dedent(
            """\
            -- Minimal seed placeholders for local development.
            insert into users (id, role, display_name)
            values
              ('00000000-0000-0000-0000-000000000001', 'teacher', 'Teacher Demo'),
              ('00000000-0000-0000-0000-000000000002', 'student', 'Student Demo')
            on conflict (id) do nothing;
            """
        ),
        "infra/ops/README.md": textwrap.dedent(
            """\
            # Ops Notes

            ## Deploy targets
            - `apps/teacher` -> Vercel
            - `apps/learner` -> Vercel
            - `services/bff` -> managed container/runtime
            - `services/workers` -> managed container/runtime
            - `infra/supabase` -> Supabase managed PostgreSQL/Auth

            ## Monitoring baseline
            - API latency and error rate
            - event ingestion lag
            - worker dead-letter counts
            """
        ),
    }
    return files


def scaffold_tutoring_platform(target: Path, consumer_base_url: str, contracts_version: str) -> None:
    files = build_files(consumer_base_url=consumer_base_url, contracts_version=contracts_version)
    for relative_path, content in files.items():
        write_file(target, relative_path, content)


def main() -> int:
    args = parse_args()
    target = Path(args.target).expanduser().resolve()
    contracts_version = resolve_contract_version(args.contracts_version, args.contracts_version_file)
    prepare_target(target, force=args.force)
    scaffold_tutoring_platform(
        target=target,
        consumer_base_url=args.consumer_base_url,
        contracts_version=contracts_version,
    )
    print(f"Scaffold complete: {target}")
    print("Next steps:")
    print(f"  cd {target}")
    print("  cp .env.example .env")
    print("  pnpm install")
    print("  pnpm dev")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScaffoldError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
