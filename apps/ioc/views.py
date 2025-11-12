from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, CreateView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import render, redirect

from .models import IOC, SavedSearch
from .forms import IOCForm

# ---------- List ----------
class IOCListView(LoginRequiredMixin, ListView):
    model = IOC
    template_name = "ioc/index.html"
    context_object_name = "object_list"
    ordering = ["-first_seen", "-id"]
    paginate_by = 50

# ---------- Create (separate /ioc/add/ endpoint) ----------
class IOCCreateView(LoginRequiredMixin, CreateView):
    model = IOC
    form_class = IOCForm
    success_url = reverse_lazy("ioc:index")  # namespace-aware redirect

    # optional: return JSON for AJAX submits
    def form_valid(self, form):
        obj = form.save()
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":  # <-- fixed header name
            return JsonResponse({
                "id": obj.id,
                "value": obj.value,
                "ioc_type": obj.ioc_type,
                "threat_score": obj.threat_score,
                "verdict": obj.verdict or "",
                "first_seen": obj.first_seen.strftime("%Y-%m-%d %H:%M") if obj.first_seen else "",
            }, status=201)
        messages.success(self.request, "IOC added.")
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"errors": form.errors}, status=400)
        return super().form_invalid(form)

# ---------- Single URL handling GET+POST at /ioc/ioc/ (optional) ----------
class IOCIndex(LoginRequiredMixin, View):
    template_name = "ioc/index.html"

    def get(self, request):
        objects = IOC.objects.all().order_by("-first_seen", "-id")
        return render(request, self.template_name, {"object_list": objects})

    def post(self, request):
        form = IOCForm(request.POST)  # <-- fixed class name
        if form.is_valid():
            form.save()
            messages.success(request, "IOC added.")
            return redirect("ioc:index")  # redirect to list route
        objects = IOC.objects.all().order_by("-first_seen", "-id")
        return render(
            request,
            self.template_name,
            {"object_list": objects, "form_errors": form.errors},
        )

# Optional DRF viewset guard stays as you had it.
try:
    from rest_framework import viewsets, permissions
    from .serializers import IOCSerializer

    class IOCViewSet(viewsets.ReadOnlyModelViewSet):
        queryset = IOC.objects.all().order_by("-first_seen")
        serializer_class = IOCSerializer
        permission_classes = [permissions.IsAuthenticated]
except Exception:
    IOCViewSet = None

@login_required
def saved_search_list(request):
    searches = SavedSearch.objects.filter(owner=requets.user)
    return render(request, "ioc_saved_searches/list.html", {"searches": searches})

@login_required
def saved_search_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        query = request.POST.get("query")

        SavedSearch.objects.create(
            owner=request.user,
            name=name,
            query=query,
        )
        return redirect("ioc_saved_search_list")

    return render(request, "ioc_saved_searches/create.html")
