"""Check startup ordering and process replacement without a database."""

import os
import subprocess
from pathlib import Path

import pytest

ENTRYPOINT = Path(__file__).resolve().parents[1] / "docker-entrypoint.sh"


@pytest.mark.parametrize("migration_exit", [0, 23])
def test_entrypoint_migration_controls_startup(tmp_path, migration_exit):
    """Only successful migrations reach the command, preserving argv and PID."""
    alembic = tmp_path / "alembic"
    alembic.write_text(
        '#!/bin/sh\n'
        'printf "migration:%s:%s\\n" "$1" "$2"\n'
        f'exit {migration_exit}\n'
    )
    alembic.chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}"}
    with subprocess.Popen(
        [
            str(ENTRYPOINT), "sh", "-c",
            'printf "application:%s:%s\\n" "$$" "$1"',
            "probe", "argument with spaces",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == migration_exit
        assert stderr == ""
        expected = ["Applying database migrations...", "migration:upgrade:head"]
        if migration_exit == 0:
            expected.append(f"application:{process.pid}:argument with spaces")
        assert stdout.splitlines() == expected
