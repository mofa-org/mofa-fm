# Repository Guidelines

## Project Structure & Module Organization
- `backend/` hosts the Django stack: reusable apps under `backend/apps/`, settings in `backend/config/settings/`, and shared helpers in `backend/utils/`. Static assets live in `backend/static/`.
- `frontend/` is a Vite-powered Vue UI with entrypoints in `src/main.js`, domain stores in `src/stores/`, and API wrappers in `src/api/`.
- `media/` contains uploaded audio artifacts; keep large files out of version control unless explicitly required.

## Build, Test, and Development Commands
- Backend setup: `python -m venv venv && source venv/bin/activate && pip install -r backend/requirements/dev.txt`.
- Run the API: `cd backend && python manage.py runserver` (uses `config.settings.dev` by default).
- Background tasks: `cd backend && celery -A config worker -l info` once Redis is available.
- Frontend dev server: `cd frontend && npm install && npm run dev`.
- Production bundle: `cd frontend && npm run build`, inspected locally with `npm run preview`.

## Coding Style & Naming Conventions
- Python: follow PEP 8 with 4-space indentation; modules and functions stay snake_case, Django models and serializers use PascalCase. Keep app boundaries clean—shared logic goes in `backend/utils/`.
- Vue: single-file components in PascalCase (`PodcastPlayer.vue`); Pinia stores use camelCase ids. Keep global SCSS inside `src/assets/styles`.
- Apply consistent REST patterns: API endpoints in `backend/apps/*/api/` should expose plural nouns and return camelCase payloads to match the frontend.

## Testing Guidelines
- Backend relies on Django’s `TestCase`. Add a `tests/` package inside each app (e.g., `backend/apps/search/tests/test_search.py`) and run `cd backend && python manage.py test`.
- Mock external services (OpenAI, Redis) via `unittest.mock` or fixtures; do not hit live APIs in CI.
- Frontend tests are not yet scaffolded—add Vitest when introducing new UI logic and colocate specs under `src/components/__tests__/`.

## Commit & Pull Request Guidelines
- Follow the existing Conventional Commits pattern (`feat:`, `fix:`, `chore:`) as seen in `git log`.
- Scope commits narrowly, referencing modules touched (e.g., `feat(podcasts): enable waveform preview`).
- PRs must include: clear summary, screenshots or clips for UI changes, reproduction or validation steps, and links to related issues. Flag breaking changes upfront and ensure migrations are reversible.

## Configuration & Security Notes
- Environment variables are read via `python-decouple`; document any new keys in `backend/config/settings/base.py` and update deployment secrets out-of-band.
- Never commit `.env`, database dumps, or raw media exports. Use sample files (`*.example`) when demonstrating configuration.
