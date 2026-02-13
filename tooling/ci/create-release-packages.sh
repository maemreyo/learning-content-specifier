#!/usr/bin/env bash
set -euo pipefail

# create-release-packages.sh (workflow-local)
# Build LCS template release archives for each supported AI assistant and script type.
# Usage: tooling/ci/create-release-packages.sh <version>
#   Version argument should include leading 'v'.
#   Optionally set AGENTS and/or SCRIPTS env vars to limit what gets built.
#     AGENTS  : space or comma separated subset of: claude gemini copilot cursor-agent qwen opencode windsurf codex amp shai bob (default: all)
#     SCRIPTS : space or comma separated subset of: sh ps (default: both)
#   Examples:
#     AGENTS=claude SCRIPTS=sh $0 v0.2.0
#     AGENTS="copilot,gemini" $0 v0.2.0
#     SCRIPTS=ps $0 v0.2.0

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version-with-v-prefix>" >&2
  exit 1
fi
NEW_VERSION="$1"
if [[ ! $NEW_VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z\.-]+)?(\+[0-9A-Za-z\.-]+)?$ ]]; then
  echo "Version must look like v0.0.0 (supports pre-release/build metadata)" >&2
  exit 1
fi

echo "Building release packages for $NEW_VERSION"

# Create and use .genreleases directory for all build artifacts
GENRELEASES_DIR=".genreleases"
mkdir -p "$GENRELEASES_DIR"
rm -rf "$GENRELEASES_DIR"/* || true

rewrite_paths() {
  sed -E \
    -e 's@(^|[[:space:]"'"'"'(])memory/@\1.lcs/memory/@g' \
    -e 's@(^|[[:space:]"'"'"'(])factory/scripts/@\1.lcs/scripts/@g' \
    -e 's@(^|[[:space:]"'"'"'(])scripts/@\1.lcs/scripts/@g' \
    -e 's@(^|[[:space:]"'"'"'(])factory/templates/@\1.lcs/templates/@g' \
    -e 's@\.specify\.lcs/@.lcs/@g'
}

compute_sha256() {
  local target_file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$target_file" | awk '{print $1}'
    return
  fi
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$target_file" | awk '{print $1}'
    return
  fi
  if command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 "$target_file" | awk '{print $NF}'
    return
  fi
  local py_bin="python3"
  if ! command -v "$py_bin" >/dev/null 2>&1; then
    py_bin="python"
  fi
  "$py_bin" - "$target_file" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
}

write_sha256_sidecar() {
  local target_file="$1"
  local checksum_file="${target_file}.sha256"
  local hash
  hash="$(compute_sha256 "$target_file")"
  printf "%s  %s\n" "$hash" "$(basename "$target_file")" > "$checksum_file"
}

generate_commands() {
  local agent=$1 ext=$2 arg_format=$3 output_dir=$4 script_variant=$5
  mkdir -p "$output_dir"
  for template in factory/templates/commands/*.md; do
    [[ -f "$template" ]] || continue
    local name description script_command agent_script_command gate_script_command body
    name=$(basename "$template" .md)
    
    # Normalize line endings
    file_content=$(tr -d '\r' < "$template")
    
    # Extract description and script command from YAML frontmatter
    description=$(printf '%s\n' "$file_content" | awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}')
    script_command=$(printf '%s\n' "$file_content" | awk -v sv="$script_variant" '/^[[:space:]]*'"$script_variant"':[[:space:]]*/ {sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, ""); print; exit}')
    
    if [[ -z $script_command ]]; then
      echo "Warning: no script command found for $script_variant in $template" >&2
      script_command="(Missing script command for $script_variant)"
    fi
    
    # Extract agent_script command from YAML frontmatter if present
    agent_script_command=$(printf '%s\n' "$file_content" | awk '
      /^agent_scripts:$/ { in_agent_scripts=1; next }
      in_agent_scripts && /^[[:space:]]*'"$script_variant"':[[:space:]]*/ {
        sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, "")
        print
        exit
      }
      in_agent_scripts && /^[a-zA-Z]/ { in_agent_scripts=0 }
    ')

    # Extract gate_script command from YAML frontmatter if present
    gate_script_command=$(printf '%s\n' "$file_content" | awk '
      /^gate_scripts:$/ { in_gate_scripts=1; next }
      in_gate_scripts && /^[[:space:]]*'"$script_variant"':[[:space:]]*/ {
        sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, "")
        print
        exit
      }
      in_gate_scripts && /^[a-zA-Z]/ { in_gate_scripts=0 }
    ')
    
    # Replace {SCRIPT} placeholder with the script command
    body=$(printf '%s\n' "$file_content" | sed "s|{SCRIPT}|${script_command}|g")
    
    # Replace {AGENT_SCRIPT} placeholder with the agent script command if found
    if [[ -n $agent_script_command ]]; then
      body=$(printf '%s\n' "$body" | sed "s|{AGENT_SCRIPT}|${agent_script_command}|g")
    fi
    if [[ -n $gate_script_command ]]; then
      body=$(printf '%s\n' "$body" | sed "s|{GATE_SCRIPT}|${gate_script_command}|g")
    fi
    
    # Remove script sections from frontmatter while preserving YAML structure
    body=$(printf '%s\n' "$body" | awk '
      /^---$/ { print; if (++dash_count == 1) in_frontmatter=1; else in_frontmatter=0; next }
      in_frontmatter && /^scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^agent_scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^gate_scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^[a-zA-Z].*:/ && skip_scripts { skip_scripts=0 }
      in_frontmatter && skip_scripts && /^[[:space:]]/ { next }
      { print }
    ')
    
    # Apply other substitutions
    body=$(printf '%s\n' "$body" | sed "s/{ARGS}/$arg_format/g" | sed "s/__AGENT__/$agent/g" | rewrite_paths)
    
    case $ext in
      toml)
        body=$(printf '%s\n' "$body" | sed 's/\\/\\\\/g')
        { echo "description = \"$description\""; echo; echo "prompt = \"\"\""; echo "$body"; echo "\"\"\""; } > "$output_dir/lcs.$name.$ext" ;;
      md)
        echo "$body" > "$output_dir/lcs.$name.$ext" ;;
      agent.md)
        echo "$body" > "$output_dir/lcs.$name.$ext" ;;
    esac
  done
}

generate_copilot_prompts() {
  local agents_dir=$1 prompts_dir=$2
  mkdir -p "$prompts_dir"
  
  # Generate a .prompt.md file for each .agent.md file
  for agent_file in "$agents_dir"/lcs.*.agent.md; do
    [[ -f "$agent_file" ]] || continue
    
    local basename=$(basename "$agent_file" .agent.md)
    local prompt_file="$prompts_dir/${basename}.prompt.md"
    
    # Create prompt file with agent frontmatter
    cat > "$prompt_file" <<EOF
---
agent: ${basename}
---
EOF
  done
}

build_variant() {
  local agent=$1 script=$2
  local base_dir="$GENRELEASES_DIR/sdd-${agent}-package-${script}"
  echo "Building $agent ($script) package..."
  mkdir -p "$base_dir"
  
  # Copy base structure but filter scripts by variant
  SPEC_DIR="$base_dir/.lcs"
  mkdir -p "$SPEC_DIR"
  
  [[ -d memory ]] && { cp -r memory "$SPEC_DIR/"; echo "Copied memory -> .lcs"; }
  
  # Only copy the relevant script variant directory
  if [[ -d factory/scripts ]]; then
    mkdir -p "$SPEC_DIR/scripts"
    case $script in
      sh)
        [[ -d factory/scripts/bash ]] && { cp -r factory/scripts/bash "$SPEC_DIR/scripts/"; echo "Copied factory/scripts/bash -> .lcs/scripts"; }
        ;;
      ps)
        [[ -d factory/scripts/powershell ]] && { cp -r factory/scripts/powershell "$SPEC_DIR/scripts/"; echo "Copied factory/scripts/powershell -> .lcs/scripts"; }
        ;;
    esac
    # Always copy shared python tooling consumed by shell wrappers.
    [[ -d factory/scripts/python ]] && find factory/scripts/python -maxdepth 1 -type f -exec cp {} "$SPEC_DIR/scripts/" \; 2>/dev/null || true
  fi
  
  if [[ -d factory/templates ]]; then
    while IFS= read -r template_file; do
      rel_path="${template_file#factory/templates/}"
      dest="$SPEC_DIR/templates/$rel_path"
      mkdir -p "$(dirname "$dest")"
      cp "$template_file" "$dest"
    done < <(find factory/templates -type f -not -path "factory/templates/commands/*" -not -name "vscode-settings.json")
    echo "Copied templates -> .lcs/templates"
  fi

  if [[ -d contracts ]]; then
    mkdir -p "$SPEC_DIR/contracts"
    cp -r contracts/* "$SPEC_DIR/contracts/"
    echo "Copied contracts -> .lcs/contracts"
  fi
  
  # NOTE: We substitute {ARGS} internally. Outward tokens differ intentionally:
  #   * Markdown/prompt (claude, copilot, cursor-agent, opencode): $ARGUMENTS
  #   * TOML (gemini, qwen): {{args}}
  # This keeps formats readable without extra abstraction.

  case $agent in
    claude)
      mkdir -p "$base_dir/.claude/commands"
      generate_commands claude md "\$ARGUMENTS" "$base_dir/.claude/commands" "$script" ;;
    gemini)
      mkdir -p "$base_dir/.gemini/commands"
      generate_commands gemini toml "{{args}}" "$base_dir/.gemini/commands" "$script"
      [[ -f agent_templates/gemini/GEMINI.md ]] && cp agent_templates/gemini/GEMINI.md "$base_dir/GEMINI.md" ;;
    copilot)
      mkdir -p "$base_dir/.github/agents"
      generate_commands copilot agent.md "\$ARGUMENTS" "$base_dir/.github/agents" "$script"
      # Generate companion prompt files
      generate_copilot_prompts "$base_dir/.github/agents" "$base_dir/.github/prompts"
      # Create VS Code workspace settings
      mkdir -p "$base_dir/.vscode"
      [[ -f factory/templates/vscode-settings.json ]] && cp factory/templates/vscode-settings.json "$base_dir/.vscode/settings.json"
      ;;
    cursor-agent)
      mkdir -p "$base_dir/.cursor/commands"
      generate_commands cursor-agent md "\$ARGUMENTS" "$base_dir/.cursor/commands" "$script" ;;
    qwen)
      mkdir -p "$base_dir/.qwen/commands"
      generate_commands qwen toml "{{args}}" "$base_dir/.qwen/commands" "$script"
      [[ -f agent_templates/qwen/QWEN.md ]] && cp agent_templates/qwen/QWEN.md "$base_dir/QWEN.md" ;;
    opencode)
      mkdir -p "$base_dir/.opencode/command"
      generate_commands opencode md "\$ARGUMENTS" "$base_dir/.opencode/command" "$script" ;;
    windsurf)
      mkdir -p "$base_dir/.windsurf/workflows"
      generate_commands windsurf md "\$ARGUMENTS" "$base_dir/.windsurf/workflows" "$script" ;;
    codex)
      mkdir -p "$base_dir/.codex/commands"
      generate_commands codex md "\$ARGUMENTS" "$base_dir/.codex/commands" "$script" ;;
    kilocode)
      mkdir -p "$base_dir/.kilocode/rules"
      generate_commands kilocode md "\$ARGUMENTS" "$base_dir/.kilocode/rules" "$script" ;;
    auggie)
      mkdir -p "$base_dir/.augment/rules"
      generate_commands auggie md "\$ARGUMENTS" "$base_dir/.augment/rules" "$script" ;;
    roo)
      mkdir -p "$base_dir/.roo/rules"
      generate_commands roo md "\$ARGUMENTS" "$base_dir/.roo/rules" "$script" ;;
    codebuddy)
      mkdir -p "$base_dir/.codebuddy/commands"
      generate_commands codebuddy md "\$ARGUMENTS" "$base_dir/.codebuddy/commands" "$script" ;;
    qoder)
      mkdir -p "$base_dir/.qoder/commands"
      generate_commands qoder md "\$ARGUMENTS" "$base_dir/.qoder/commands" "$script" ;;
    amp)
      mkdir -p "$base_dir/.agents/commands"
      generate_commands amp md "\$ARGUMENTS" "$base_dir/.agents/commands" "$script" ;;
    shai)
      mkdir -p "$base_dir/.shai/commands"
      generate_commands shai md "\$ARGUMENTS" "$base_dir/.shai/commands" "$script" ;;
    q)
      mkdir -p "$base_dir/.amazonq/prompts"
      generate_commands q md "\$ARGUMENTS" "$base_dir/.amazonq/prompts" "$script" ;;
    bob)
      mkdir -p "$base_dir/.bob/commands"
      generate_commands bob md "\$ARGUMENTS" "$base_dir/.bob/commands" "$script" ;;
  esac
  ( cd "$base_dir" && zip -r "../learning-content-specifier-template-${agent}-${script}-${NEW_VERSION}.zip" . )
  local zip_path="$GENRELEASES_DIR/learning-content-specifier-template-${agent}-${script}-${NEW_VERSION}.zip"
  write_sha256_sidecar "$zip_path"
  echo "Created $zip_path"
}

# Determine agent list
ALL_AGENTS=(claude gemini copilot cursor-agent qwen opencode windsurf codex kilocode auggie roo codebuddy amp shai q bob qoder)
ALL_SCRIPTS=(sh ps)

norm_list() {
  # convert comma+space separated -> line separated unique while preserving order of first occurrence
  tr ',\n' '  ' | awk '{for(i=1;i<=NF;i++){if(!seen[$i]++){printf((out?"\n":"") $i);out=1}}}END{printf("\n")}'
}

validate_subset() {
  local type=$1
  local allowed_csv=$2
  shift 2
  local items=("$@")
  local invalid=0
  for it in "${items[@]}"; do
    local found=0
    for a in $allowed_csv; do [[ $it == "$a" ]] && { found=1; break; }; done
    if [[ $found -eq 0 ]]; then
      echo "Error: unknown $type '$it' (allowed: $allowed_csv)" >&2
      invalid=1
    fi
  done
  return $invalid
}

if [[ -n ${AGENTS:-} ]]; then
  AGENT_LIST=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && AGENT_LIST+=("$line")
  done < <(printf '%s' "$AGENTS" | norm_list)
  validate_subset agent "${ALL_AGENTS[*]}" "${AGENT_LIST[@]}" || exit 1
else
  AGENT_LIST=("${ALL_AGENTS[@]}")
fi

if [[ -n ${SCRIPTS:-} ]]; then
  SCRIPT_LIST=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && SCRIPT_LIST+=("$line")
  done < <(printf '%s' "$SCRIPTS" | norm_list)
  validate_subset script "${ALL_SCRIPTS[*]}" "${SCRIPT_LIST[@]}" || exit 1
else
  SCRIPT_LIST=("${ALL_SCRIPTS[@]}")
fi

echo "Agents: ${AGENT_LIST[*]}"
echo "Scripts: ${SCRIPT_LIST[*]}"

for agent in "${AGENT_LIST[@]}"; do
  for script in "${SCRIPT_LIST[@]}"; do
    build_variant "$agent" "$script"
  done
done

if command -v uv >/dev/null 2>&1; then
  uv run python factory/scripts/python/build_contract_package.py --verify --package-version "$NEW_VERSION" --output-dir "$GENRELEASES_DIR"
else
  PYTHON_BIN="python3"
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    PYTHON_BIN="python"
  fi
  "$PYTHON_BIN" factory/scripts/python/build_contract_package.py --verify --package-version "$NEW_VERSION" --output-dir "$GENRELEASES_DIR"
fi
write_sha256_sidecar "$GENRELEASES_DIR/lcs-contracts-${NEW_VERSION}.zip"

echo "Archives in $GENRELEASES_DIR:"
ls -1 "$GENRELEASES_DIR"/learning-content-specifier-template-*-"${NEW_VERSION}".zip
ls -1 "$GENRELEASES_DIR"/lcs-contracts-"${NEW_VERSION}".zip
ls -1 "$GENRELEASES_DIR"/*.sha256
