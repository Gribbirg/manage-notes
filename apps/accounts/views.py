from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, RegistrationForm
from django.contrib.auth.backends import ModelBackend


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('notes:list')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                # Redirect to the page user was trying to access, or default to notes list
                next_page = request.GET.get('next', 'notes:list')
                return redirect(next_page)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('notes:list')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in right after registration with specified backend
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Account created successfully. Welcome, {user.username}!")
            return redirect('notes:list')
    else:
        form = RegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    """View and edit user profile."""
    return render(request, 'accounts/profile.html')


@login_required
def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')
