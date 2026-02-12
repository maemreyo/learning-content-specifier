import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tooling/ci/check-consumer-contract-compat.sh"


@pytest.mark.skipif(os.name == "nt", reason="bash script")
def test_consumer_contract_compat_uses_pinned_file_when_env_missing():
    env = os.environ.copy()
    env.pop("CONSUMER_CONTRACT_VERSION", None)
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "source=contracts/consumer-contract-version.txt" in result.stdout


@pytest.mark.skipif(os.name == "nt", reason="bash script")
def test_consumer_contract_compat_blocks_major_mismatch():
    env = os.environ.copy()
    env["CONSUMER_CONTRACT_VERSION"] = "2.0.0"
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Contract major mismatch" in result.stderr
