import time
from django.core.management.base import BaseCommand
from problems.models import Problem
from problems.services import fetch_problem_by_id, CodeforcesAPIError


class Command(BaseCommand):
    help = 'Fetch codeforces problem rating for problems in the database and update Problem.codeforces_rating (supports an --estimate mode)'

    def add_arguments(self, parser):
        parser.add_argument('--delay', type=float, default=0.2, help='Delay between API calls in seconds')
        parser.add_argument('--dry-run', action='store_true', help='Do not save changes')
        parser.add_argument('--estimate', action='store_true', help='Estimate missing CF ratings from site data when API has none')

    def handle(self, *args, **options):
        delay = options['delay']
        dry_run = options['dry_run']
        do_estimate = options['estimate']

        problems = Problem.objects.all()
        total = problems.count()
        updated = 0
        already = 0
        missing = 0
        estimated = 0
        failed = 0

        self.stdout.write(f'Checking {total} problems')
        for p in problems:
            try:
                data = fetch_problem_by_id(p.problem_id)
                new_rating = data.get('rating')
                if new_rating is None:
                    missing += 1
                    # If requested, estimate from site average rating (user ratings) if available
                    if do_estimate:
                        if p.average_rating and p.average_rating > 0:
                            # Map user 0-10 scale to CF rating 800-3500 linearly
                            estimated_val = int(round(800 + p.average_rating * 270))
                            if estimated_val != p.codeforces_rating or not p.codeforces_rating_estimated:
                                self.stdout.write(f'Estimating {p.problem_id}: {p.codeforces_rating} -> {estimated_val} (from avg {p.average_rating})')
                                if not dry_run:
                                    p.codeforces_rating = estimated_val
                                    p.codeforces_rating_estimated = True
                                    p.save(update_fields=['codeforces_rating', 'codeforces_rating_estimated'])
                                estimated += 1
                        else:
                            # no data to estimate
                            pass
                else:
                    # API provided a rating
                    if new_rating != p.codeforces_rating or p.codeforces_rating_estimated:
                        self.stdout.write(f'Updating {p.problem_id}: {p.codeforces_rating} -> {new_rating}')
                        if not dry_run:
                            p.codeforces_rating = new_rating
                            p.codeforces_rating_estimated = False
                            p.save(update_fields=['codeforces_rating', 'codeforces_rating_estimated'])
                        updated += 1
                    else:
                        already += 1
                time.sleep(delay)
            except CodeforcesAPIError as e:
                self.stderr.write(f'Failed to fetch {p.problem_id}: {e}')
                failed += 1

        self.stdout.write('--- Summary ---')
        self.stdout.write(f'Total checked: {total}')
        self.stdout.write(f'API-updated: {updated}')
        self.stdout.write(f'Already had rating: {already}')
        self.stdout.write(f'Missing from API: {missing}')
        self.stdout.write(f'Estimated (with --estimate): {estimated}')
        self.stdout.write(f'Failed: {failed}')
        self.stdout.write(self.style.SUCCESS('Done'))
