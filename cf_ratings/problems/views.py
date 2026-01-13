from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q

from .forms import RegisterForm, UserProfileForm, AddProblemForm, RatingForm
from .models import UserProfile, Problem, Tag, Rating, UserProblem
from .services import fetch_user_info, fetch_problem_by_id, CodeforcesAPIError


class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful.')
            return redirect('home')
        return render(request, 'register.html', {'form': form})


class LoginView(DjangoLoginView):
    template_name = 'login.html'


class LogoutView(View):
    """Explicit logout view to ensure deterministic redirect and message."""
    def get(self, request):
        auth_logout(request)
        messages.success(request, 'Logged out successfully.')
        return redirect('home')


class HomeView(ListView):
    model = Problem
    template_name = 'home.html'
    context_object_name = 'problems'

    def get_queryset(self):
        # Ensure unique problems and sort by average rating descending
        return Problem.objects.prefetch_related('tags').order_by('-average_rating').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rating_choices'] = list(range(0, 11))
        problems = list(context.get('problems', []))
        if self.request.user.is_authenticated:
            user_ratings = Rating.objects.filter(user=self.request.user, problem__in=problems)
            rating_map = {r.problem.problem_id: r.value for r in user_ratings}
            user_problems = UserProblem.objects.filter(user=self.request.user, problem__in=problems)
            status_map = {up.problem.problem_id: up.status for up in user_problems}
        else:
            rating_map = {}
            status_map = {}
        # Attach user's rating and status (if any) to each problem object for easy template access
        for p in problems:
            p.user_rating = rating_map.get(p.problem_id)
            p.user_status = status_map.get(p.problem_id)
        context['problems'] = problems
        return context


class RateProblemView(LoginRequiredMixin, View):
    def post(self, request, problem_id):
        problem = get_object_or_404(Problem, problem_id__iexact=problem_id)
        # Do not create an empty Rating (value is NOT NULL). Use form to validate input first,
        # then create or update the Rating instance.
        existing = Rating.objects.filter(user=request.user, problem=problem).first()
        if existing:
            form = RatingForm(request.POST, instance=existing)
        else:
            form = RatingForm(request.POST)

        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            rating.problem = problem
            rating.save()
            messages.success(request, 'Rating saved.')
        else:
            messages.error(request, 'Invalid rating.')
        # Respect 'next' parameter to allow returning to the page where rating was submitted
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('problem_detail', problem_id=problem.problem_id)


class UserListView(ListView):
    model = User
    template_name = 'users_list.html'
    context_object_name = 'users'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = list(context.get('users', []))
        users_data = []
        for u in users:
            profile, _ = UserProfile.objects.get_or_create(user=u)
            # unique problems the user has added
            added = set(UserProblem.objects.filter(user=u).values_list('problem__problem_id', flat=True))
            # unique problems the user has rated
            rated = set(Rating.objects.filter(user=u).values_list('problem__problem_id', flat=True))
            contrib_count = len(added.union(rated))
            # compute star tier (natural mapping)
            if contrib_count >= 500:
                stars = 5
            elif contrib_count >= 200:
                stars = 4
            elif contrib_count >= 100:
                stars = 3
            elif contrib_count >= 50:
                stars = 2
            elif contrib_count >= 20:
                stars = 1
            else:
                stars = 0
            users_data.append({
                'user': u,
                'profile': profile,
                'contrib_count': contrib_count,
                'stars': stars,
            })
        # Sort users by contributor count (descending)
        users_data.sort(key=lambda x: x['contrib_count'], reverse=True)
        context['users_data'] = users_data
        return context


class ProfileView(View):
    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        cf_data = None
        if profile.codeforces_handle:
            try:
                cf_data = fetch_user_info(profile.codeforces_handle)
            except CodeforcesAPIError as e:
                messages.error(request, f"Codeforces fetch error: {e}")
        form = None
        if request.user.username == username:
            form = UserProfileForm(instance=profile)
        # list problems this user has added or rated
        rated = Rating.objects.filter(user=user).select_related('problem')
        rating_map = {r.problem.problem_id: r.value for r in rated}
        user_problems = Problem.objects.filter(Q(user_problems__user=user) | Q(ratings__user=user)).distinct().prefetch_related('tags').order_by('-average_rating')
        # attach user's rating (if any) and status to each problem for template access
        user_problem_objs = UserProblem.objects.filter(user=user, problem__in=user_problems)
        status_map = {up.problem.problem_id: up.status for up in user_problem_objs}
        for p in user_problems:
            p.user_rating = rating_map.get(p.problem_id)
            p.user_status = status_map.get(p.problem_id)
        # expose rating choices for the template's rating form
        return render(request, 'profile.html', {'profile_user': user, 'profile': profile, 'cf_data': cf_data, 'form': form, 'user_problems': user_problems, 'rating_choices': list(range(0, 11))})

    def post(self, request, username):
        # edit profile (only owner)
        if request.user.username != username:
            messages.error(request, 'Permission denied.')
            return redirect('profile', username=username)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            p = form.save()
            # fetch CF data
            if p.codeforces_handle:
                try:
                    data = fetch_user_info(p.codeforces_handle)
                    p.rating = data.get('rating')
                    p.max_rating = data.get('maxRating')
                    p.rank = data.get('rank')
                    p.max_rank = data.get('maxRank')
                    p.save()
                    messages.success(request, 'Profile updated and Codeforces data fetched.')
                except CodeforcesAPIError as e:
                    messages.warning(request, f'Profile saved but Codeforces fetch failed: {e}')
            else:
                messages.success(request, 'Profile updated.')
            return redirect('profile', username=username)
        return render(request, 'profile_edit.html', {'form': form})


class AddProblemView(LoginRequiredMixin, View):
    def get(self, request):
        form = AddProblemForm()
        return render(request, 'add_problem.html', {'form': form})

    def post(self, request):
        form = AddProblemForm(request.POST)
        if form.is_valid():
            pid = form.cleaned_data['problem_id'].upper()
            # If the problem already exists in DB, attach it to the user's collection instead of erroring
            problem_obj = Problem.objects.filter(problem_id__iexact=pid).first()
            if problem_obj:
                # Attach to user's collection
                from .models import UserProblem
                up, created = UserProblem.objects.get_or_create(user=request.user, problem=problem_obj)
                if created:
                    messages.success(request, 'Problem already existed — added to your collection.')
                else:
                    messages.info(request, 'Problem already in your collection.')
                return redirect('problem_detail', problem_id=problem_obj.problem_id)

            try:
                p = fetch_problem_by_id(pid)
                name = p.get('name')
                contest_id = p.get('contestId')
                index = p.get('index')
                tags = p.get('tags', [])
                problem_obj = Problem.objects.create(
                    name=name, problem_id=pid, contest_id=contest_id, index=index, owner=request.user,
                    codeforces_rating=p.get('rating')
                )
                for t in tags:
                    tag_obj, _ = Tag.objects.get_or_create(name=t)
                    problem_obj.tags.add(tag_obj)
                # Add to user's collection
                from .models import UserProblem
                UserProblem.objects.get_or_create(user=request.user, problem=problem_obj)
                messages.success(request, 'Problem added successfully.')
                return redirect('problem_detail', problem_id=problem_obj.problem_id)
            except CodeforcesAPIError as e:
                messages.error(request, f'Error fetching problem: {e}')
        return render(request, 'add_problem.html', {'form': form})


class ProblemDetailView(View):
    def get(self, request, problem_id):
        problem = get_object_or_404(Problem, problem_id__iexact=problem_id)
        rating_form = None
        user_rating = None
        if request.user.is_authenticated:
            user_rating = Rating.objects.filter(user=request.user, problem=problem).first()
            rating_form = RatingForm(instance=user_rating)
        return render(request, 'problem_detail.html', {'problem': problem, 'rating_form': rating_form, 'user_rating': user_rating})


class RateProblemView(LoginRequiredMixin, View):
    def post(self, request, problem_id):
        problem = get_object_or_404(Problem, problem_id__iexact=problem_id)
        # Do not create an empty Rating (value is NOT NULL). Use form to validate input first,
        # then create or update the Rating instance.
        existing = Rating.objects.filter(user=request.user, problem=problem).first()
        if existing:
            form = RatingForm(request.POST, instance=existing)
        else:
            form = RatingForm(request.POST)

        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            rating.problem = problem
            rating.save()
            messages.success(request, 'Rating saved.')
        else:
            messages.error(request, 'Invalid rating.')
        return redirect('problem_detail', problem_id=problem.problem_id)


class SearchView(View):
    def get(self, request):
        tag = request.GET.get('tag')
        pid = request.GET.get('problem_id')
        results = None
        tags = Tag.objects.order_by('name')
        id_query = None
        id_not_found = False

        # If a problem_id was provided, prioritize ID lookup
        if pid is not None:
            pid = (pid or '').strip()
            id_query = pid.upper() if pid else ''
            if id_query:
                problem_obj = Problem.objects.filter(problem_id__iexact=id_query).first()
                if problem_obj:
                    results = [problem_obj]
                else:
                    id_not_found = True

        # If no ID search (or empty ID), fall back to tag search logic
        if (pid is None) or (pid is not None and id_query == ''):
            if tag is not None:
                if tag == '':
                    results = Problem.objects.order_by('-average_rating')
                else:
                    results = Problem.objects.filter(tags__name__iexact=tag).order_by('-average_rating')

        context = {'query': tag, 'tags': tags, 'id_query': id_query, 'id_not_found': id_not_found}
        # If we have results, attach user-specific info for display (ratings and status)
        if results is not None:
            problems = list(results)
            context['rating_choices'] = list(range(0, 11))
            if request.user.is_authenticated:
                user_ratings = Rating.objects.filter(user=request.user, problem__in=problems)
                rating_map = {r.problem.problem_id: r.value for r in user_ratings}
                user_problem_objs = UserProblem.objects.filter(user=request.user, problem__in=problems)
                status_map = {up.problem.problem_id: up.status for up in user_problem_objs}
            else:
                rating_map = {}
                status_map = {}
            for p in problems:
                p.user_rating = rating_map.get(p.problem_id)
                p.user_status = status_map.get(p.problem_id)
            context['results'] = problems
        else:
            context['results'] = None
        return render(request, 'search.html', context)


class MarkProblemView(LoginRequiredMixin, View):
    """Mark a problem as pending/solved for the logged-in user."""
    def post(self, request, problem_id):
        status = request.POST.get('status')
        if status not in (UserProblem.STATUS_PENDING, UserProblem.STATUS_SOLVED):
            messages.error(request, 'Invalid status.')
            return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'home')
        problem = get_object_or_404(Problem, problem_id__iexact=problem_id)
        up, _ = UserProblem.objects.get_or_create(user=request.user, problem=problem)
        up.status = status
        up.save()
        messages.success(request, f'Problem marked as {status}.')
        return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'home')