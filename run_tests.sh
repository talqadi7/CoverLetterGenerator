#!/bin/bash
# This script runs the tests and the linter.

# Stop the script if any command fails.
set -e

# Run the tests.
echo "Running tests..."
pytest

# Run the linter.
echo "Checking code quality..."
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

echo "All checks passed!"
