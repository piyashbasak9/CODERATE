# CF Ratings

Community-powered ratings for Codeforces problems.

## Overview
CF Ratings lets users add Codeforces problems to a shared catalog, rate their perceived difficulty (0–10), and view community averages. The app also attempts to surface Codeforces' official problem rating when available and can estimate ratings when Codeforces doesn't provide them.

## Features
- Add problems from Codeforces by problem ID (e.g., `1234A`).
- Browse and search problems by tag or problem ID.
- Save personal problem status (pending / solved) and per-problem rating (0–10).
- Show community average rating per problem.
- Store and display Codeforces' official rating (when present).
- Optional estimation mode to fill missing Codeforces ratings using site user averages.
- Management command to fetch/update Codeforces ratings for all problems.

## Tech stack
- Python 3.12
- Django 6.x
- Bulma CSS for the frontend
- Requests for Codeforces API access

## Quickstart (development)
1. Clone the repo:
   ```bash
   git clone https://github.com/piyashbasak9/CODERATE.git
   cd CODERATE/cf_ratings
   ```

2. Create a virtualenv (recommended):
   ```bash
   python3 -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   ```

3. Apply database migrations:
   ```bash
   env/bin/python3 manage.py migrate
   ```

4. Create a superuser (optional):
   ```bash
   env/bin/python3 manage.py createsuperuser
   ```

5. Run the development server:
   ```bash
   env/bin/python3 manage.py runserver
   ```

6. Open http://127.0.0.1:8000/ in your browser.

## Important pages / URLs
- Home (problem list): `/`
- Search (by tag or problem ID): `/search`
- Add problem (signed-in users): `/add/` (via UI)
- Problem detail: `/problems/<problem_id>/`
- User profile: `/profile/<username>/`

## Management commands
- `manage.py fetch_cf_ratings` — Fetch Codeforces rating data for problems in DB.
  - Options:
    - `--dry-run` — do not persist changes (preview only)
    - `--estimate` — when Codeforces API lacks a rating, estimate one from user average
    - `--delay <seconds>` — delay between API calls (default: 0.2)

Example:
```bash
# Dry-run estimate preview
env/bin/python3 manage.py fetch_cf_ratings --dry-run --estimate

# Apply estimates/pulls to DB
env/bin/python3 manage.py fetch_cf_ratings --estimate
```

Notes on estimation:
- Estimation maps the internal user-average (0–10) scale to a Codeforces-like rating (approx. 800–3500) using a linear formula. Estimated values are marked in the UI with `(est)`.

## Tests & checks
- Run Django system checks:
  ```bash
  env/bin/python3 manage.py check
  ```

- There are no automated test suites included yet; consider adding unit and integration tests for future work.

## Development notes & suggestions
- Consider adding `env/` to `.gitignore` to avoid committing virtual environments.
- The Codeforces API does not always include a `rating` field for problems; the app handles this gracefully and can optionally estimate ratings.
- To periodically refresh CF ratings, run the management command on a schedule (cron, CI job, or background worker).

## Contributing
- Fork the repo, create a feature branch, and open a PR with tests and a clear description.

## License
MIT (add a LICENSE file if you want an explicit license).

---

Maintainer: Piyash Basak — piyashbasak99@gmail.com
