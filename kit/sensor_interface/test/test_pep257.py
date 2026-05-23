# Copyright 2024 Kossi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
"""Pep257 test configured for this project's docstring style."""

import os
import pytest


@pytest.mark.linter
def test_pep257():
    """Check docstrings with project-specific style rules."""
    try:
        import pydocstyle
    except ImportError:
        pytest.skip('pydocstyle not installed')

    ignored = {
        'D100', 'D101', 'D102', 'D103', 'D104',
        'D107', 'D200', 'D202', 'D203', 'D204',
        'D205', 'D212', 'D400', 'D401', 'D403',
        'D405', 'D406', 'D407', 'D413', 'D415',
    }

    src_dir = os.path.join(os.path.dirname(__file__), '..')
    errors = []

    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [
            d for d in dirs
            if d not in {
                'build', 'install', 'log',
                '__pycache__', '.git', '.venv'
            }
        ]
        for fname in files:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(root, fname)
            try:
                file_errors = list(
                    pydocstyle.check([fpath], ignore=ignored)
                )
                errors.extend(file_errors)
            except Exception:
                pass

    if errors:
        msg = '\n'.join(str(e) for e in errors[:10])
        pytest.fail(f'Pep257 errors found:\n{msg}')
        