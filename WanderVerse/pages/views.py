from django.shortcuts import render

# Create your views here.
def index(request):
    # Get all societies to render on landing page Societies section

    return render(
        request, "pages/index.html",
    )