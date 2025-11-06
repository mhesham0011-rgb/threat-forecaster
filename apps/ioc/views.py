from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.http import JsonResponse
from django.urls import reverse_lazy
from .models import IOC
from .forms import IOCForm
from apps.audit.utils import write_audit

class IOCListView(LoginRequiredMixin, ListView):
    model = IOC
    template_name = "ioc/index.html"
    context_object_name = "object_list"
    ordering = ["-first_seen"]
    paginate_by = 50

class IOCCreateView(LoginRequiredMixin, CreateView):
    form_class = IOCForm
    template_name = "ioc/index.html"
    success_url = reverse_lazy("ioc:index")

    def form_valid(self, form):
        obj = form.save()

        # AJAX response to update DataTabele without reload
        if self.request.headers.get("x-requested-width") == "XMLHttpRequest":
            return JsonResponse({
                "id": obj.id,
                "value": obj.value,
                "ioc_type": obj.ioc_type,
                "threat_score": obj.threat_score,
                "verdict": obj.verdict or "",
                "first_seen": obj.first_seen.strftime("%Y-%m-%d %H:%M") if obj.first_seen else "",
            }, status=201)
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"errors": form.errors}, status=400)
        return super().form_invalid(form)

IOCViewSet = None
try:
    from rest_framework import viewsets, permissions
    from .serializers import IOCSerializer

    class IOCViewSet(viewsets.ReadOnlyModelViewSet):
        queryset = IOC.objects.all().order_by("-first_seen")
        serializer_class = IOCSerializer
        permission_classes = [permissions.IsAuthenticated]
except Exception:
    # Leave IOCViewSet = None so imports succeed even if DRF isn't installed yet.
    pass
