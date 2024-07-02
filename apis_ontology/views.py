from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from auditlog.models import LogEntry


class UserAuditLog(LoginRequiredMixin, ListView):
    def get_queryset(self, *args, **kwargs):
        return LogEntry.objects.filter(actor=self.request.user)
