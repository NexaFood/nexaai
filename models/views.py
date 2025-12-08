def login_view(request):
    """Custom login view for MongoDB authentication."""
    if request.method == 'GET':
        # If already logged in, redirect to home
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, 'registration/login.html')
    
    # POST - Handle login
    from django.contrib.auth import authenticate, login
    
    username = request.POST.get('username', '').strip().lower()  # Convert to lowercase
    password = request.POST.get('password', '')
    
    # Validation
    if not username or not password:
        context = {
            'error': 'Username and password are required',
            'username': username
        }
        return render(request, 'registration/login.html', context)
    
    # Authenticate user
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        # Login successful
        login(request, user)
        
        # Redirect to next page or home
        next_url = request.GET.get('next', '/')
        return redirect(next_url)
    else:
        # Login failed
        context = {
            'error': 'Invalid username or password',
            'username': username
        }
        return render(request, 'registration/login.html', context)
