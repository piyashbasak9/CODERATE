from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    codeforces_handle = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    max_rating = models.IntegerField(blank=True, null=True)
    rank = models.CharField(max_length=50, blank=True, null=True)
    max_rank = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.codeforces_handle})" if self.codeforces_handle else self.user.username


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Problem(models.Model):
    name = models.CharField(max_length=255)
    problem_id = models.CharField(max_length=20, unique=True)  # e.g., 2184G
    contest_id = models.IntegerField()
    index = models.CharField(max_length=10)
    tags = models.ManyToManyField(Tag, related_name='problems')
    average_rating = models.FloatField(default=0.0)
    # Codeforces-provided difficulty rating (e.g., 1600). Nullable if not known.
    codeforces_rating = models.IntegerField(blank=True, null=True)
    # Whether the `codeforces_rating` value was estimated by the application (not provided by Codeforces).
    codeforces_rating_estimated = models.BooleanField(default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='owned_problems')

    def __str__(self):
        return f"{self.name} ({self.problem_id})"

    def update_average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            avg = sum([r.value for r in ratings]) / ratings.count()
            self.average_rating = round(avg, 2)
        else:
            self.average_rating = 0.0
        self.save(update_fields=['average_rating'])


class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='ratings')
    value = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])

    class Meta:
        unique_together = ('user', 'problem')

    def __str__(self):
        return f"{self.user.username} -> {self.problem.problem_id}: {self.value}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalculate average rating when a rating is created/updated
        self.problem.update_average_rating()


class UserProblem(models.Model):
    """Represents that a user has added/connected to a Problem in the site.
    A Problem record is unique per Codeforces problem; multiple users can add it to their collection via this model.
    """
    STATUS_PENDING = 'pending'
    STATUS_SOLVED = 'solved'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SOLVED, 'Solved'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_problems')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='user_problems')
    added_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, null=True)

    class Meta:
        unique_together = ('user', 'problem')

    def __str__(self):
        if self.status:
            return f"{self.user.username} {self.status} {self.problem.problem_id}"
        return f"{self.user.username} added {self.problem.problem_id}"
