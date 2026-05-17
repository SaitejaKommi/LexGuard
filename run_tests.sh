#!/bin/bash
set -e
echo "Running LexGuard test suite..."
python -m pytest tests/ -v --tb=short
EXIT_CODE=$?
echo "Tests finished with exit code $EXIT_CODE"
exit $EXIT_CODE
