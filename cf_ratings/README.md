# CF Ratings

Simple Django app to add and rate Codeforces problems.

Setup:

1. Create virtualenv: python -m venv venv
2. Activate: source venv/bin/activate
3. Install: pip install django requests Pillow
4. Run migrations: python manage.py migrate
5. Run server: python manage.py runserver

Notes on media:
- Uploaded profile pictures are saved to the `media/` directory.
- In development, Django serves media when `DEBUG = True`.

Notes:
- Uses Codeforces public API; no API key needed.
- Default DB is sqlite.
