import time
from django.core.management.base import BaseCommand
from problems.models import Problem
from problems.services import fetch_problem_by_id, CodeforcesAPIError


class Command(BaseCommand):
    help = 'Fetch codeforces problem rating for problems in the database and update Problem.codeforces_rating'

    def add_arguments(self, parser):
        parser.add_argument('--delay', type=float, default=0.2, help='Delay between API calls in seconds')
        parser.add_argument('--dry-run', action='store_true', help='Do not save changes')

    def handle(self, *args, **options):
        delay = options['delay']
        dry_run = options['dry_run']
        problems = Problem.objects.all()
        updated = 0
        failed = 0
        self.stdout.write(f'Found {problems.count()} problems to check')
        for p in problems:
            try:
                data = fetch_problem_by_id(p.problem_id)
                new_rating = data.get('rating')
                if new_rating != p.codeforces_rating:
                    self.stdout.write(f'Updating {p.problem_id}: {p.codeforces_rating} -> {new_rating}')
                    if not dry_run:
                        p.codeforces_rating = new_rating
                        p.save(update_fields=['codeforces_rating'])
                    updated += 1
                time.sleep(delay)
            except CodeforcesAPIError as e:
                self.stderr.write(f'Failed to fetch {p.problem_id}: {e}')
                failed += 1
        self.stdout.write(self.style.SUCCESS(f'Finished: {updated} updated, {failed} failed'))
