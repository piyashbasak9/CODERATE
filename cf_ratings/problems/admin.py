from django.contrib import admin
from .models import UserProfile, Tag, Problem, Rating

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'codeforces_handle', 'rating', 'max_rating', 'rank', 'max_rank')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('name', 'problem_id', 'contest_id', 'index', 'average_rating', 'owner')
    search_fields = ('name', 'problem_id')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'problem', 'value')
