from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile, Rating

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, **kwargs):
    # Ensure a profile exists for the user (safe for users created before signals)
    UserProfile.objects.get_or_create(user=instance)

@receiver(post_delete, sender=Rating)
def update_problem_average_on_rating_delete(sender, instance, **kwargs):
    """Recalculate a problem's average rating when a Rating is deleted."""
    problem = instance.problem
    try:
        problem.update_average_rating()
    except Exception:
        # Avoid crashing on delete; log or pass in production
        pass
