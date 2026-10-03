# AGENT_USAGE

## Project
Grant Application Completeness Assistant

## AI-assisted development
AI assistance was used during development for:
- Reviewing and improving backend service logic.
- Debugging FastAPI/API behavior.
- Reviewing frontend rendering and interaction issues.
- Generating and refining test cases.
- Reviewing project structure, validation, and error handling.
- Improving documentation and development workflow.

## Human review
All AI-generated suggestions were reviewed and adapted manually before being included in the project.

## Verification
The project was verified locally using:
- Backend pytest test suite.
- FastAPI API checks.
- Frontend Vite build.
- Manual frontend assessment/review flow testing.

## Important implementation decisions
- AI suggestions are treated as reviewable outputs rather than final decisions.
- Human review actions are stored separately from the original AI result.
- Completeness is calculated deterministically from the current reviewed state.
- Stale clarification questions are removed when their underlying requirement status changes.

## Secrets
No API keys, credentials, or other secrets are intentionally committed to the repository.
Environment-specific values should be supplied through environment variables.
