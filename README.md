# Autosuite Service

![Python 3.12](https://img.shields.io/badge/python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-async%20API-009688?logo=fastapi)
![Playwright](https://img.shields.io/badge/Playwright-E2E%20Automation-2EAD33?logo=microsoft-playwright)
![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions)
![pytest](https://img.shields.io/badge/tests-pytest%20%7C%20Ruff%20%7C%20Black%20%7C%20Mypy-0A9EDC?logo=pytest)
![Coverage ≥ 70%](https://img.shields.io/badge/coverage-%E2%89%A5%2070%25-4CAF50)
![CI](https://github.com/tranvan1202/autosuite-service/actions/workflows/ci.yml/badge.svg)

## TL;DR
A lightweight automation service that runs browser tasks using FastAPI and Playwright.
It follows a clean structure with Page Objects, background job handling, and reliable CI checks.

## Why this service exists
The service is designed to make automation easier for both technical and non-technical teams (stakeholders, QA manual testers, business operations).

Users can provide simple input data, and the system will run the flow and return structured results and reports.

This helps reduce repetitive work and keeps results consistent across teams.

## What this project demonstrates
- Reusable Page Object Model for UI steps
- Browser execution via Playwright with stable waits and retry handling.
- FastAPI workers handling jobs in the background
- Logging, metrics, and captured artifacts on failures
- CI checks for linting, typing, and test coverage
- Automation as a service for non-tech users, helps non-technical teams run repeatable automated flows.

> **Architecture note:**  
> Playwright flows and Page Objects are part of the application, not just test code.  
> They run as real tasks triggered by users, so they belong in the service layer rather than in the test suite.

> **Security note:**  
> - Only simple or demo flows are included in this repository.
> - Flows that contain sensitive logic, internal business rules, or protected data are not stored here.
> - They can be added privately or deployed separately as needed.

## Tech Stack
- **Python 3.12**
- **FastAPI + Pydantic:** for API and job control
- **Playwright (Python):** for browser automation
- **pytest:** unit, integration, and E2E test runner
- **Quality tools:** Ruff, Black, Mypy, pytest-cov, GitHub Actions.

## Quickstart
### Setup (On Windows)
1. **Create virtual environment**
   ```bash
    py -3.12 -m venv .venv
   ```
2. **Activate environment**
   ```bash
   .\.venv\Scripts\Activate.ps1
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt -r dev-requirements.txt
   playwright install
   ```
4. **Start the service**
   ```bash
   python -m uvicorn service.app.main:app --reload
   ```
5. **Run tests**
   ```bash
   pytest
   ```

## Sample Features / Flows
- **E-commerce smoke (Sauce Demo):** Login, add items to cart, go through checkout, and verify totals.
- **Simple crawler:** Visit web pages, extract data, store results, and expose them through the API.

## Testing & CI
- Separate layers: unit tests, integration tests, and Playwright E2E tests.
- Coverage target ≥ 70% checked in CI.
- All pushes run lint, type checking, and test suites before merge.
- Deployment is handled separately depending on the environment, so CI focuses mainly on code quality and test reliability.
  