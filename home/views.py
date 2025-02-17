from django.shortcuts import render


def home(request):
    """
    Renders the homepage.
    """
    return render(request, 'home/home.html')
