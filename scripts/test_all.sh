#!/usr/bin/env bash
set -e

echo "🧪 Running Unit + Integration tests..."
pytest tests/unit tests/integration \
  --junitxml=var/reports/junit-unit-integration.xml \
  --html=var/reports/unit-integration.html --self-contained-html \
  --cov=autosuite-service --cov=engine \
  --cov-report=xml:var/reports/coverage.xml

echo "🎭 Running E2E tests..."
pytest tests/e2e \
  --junitxml=var/reports/junit-e2e.xml

echo "📦 Reports stored under var/reports/"
