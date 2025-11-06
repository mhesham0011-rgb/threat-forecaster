from apps.audit.utils import write_audit

class AuditCreateMixin:
    audit_action = "object.create"
    audit_target_type = ""

    def form_valid(self, form):
        res = super().form_valid(form)
        obj = self.object
        write_audit(
            request=self.request,
            action=self.audit_action,
            target_type=self.audit_target_type or obj.__class__.__name__.lower(),
            target_id=obj.pk, target_repr=str(obj),
            message=f"Created {obj}",
            extra={"changed": list(form.changed_data) if hasattr(form, "changed_data") else []}
        )
        return res

class AuditUpdateMixin:
    audit_action = "object.update"
    audit_target_type = ""

    def form_valid(self, form):
        res = super().form_valid(form)
        obj = self.object
        write_audit(
            request=self.request,
            action=self.audit_action,
            target_type=self.audit_target_type or obj.__class__.__name__.lower(),
            target_id=obj.pk, target_repr=str(obj),
            message=f"Updated {obj}",
            extra={"changed": list(form.changed_data)}
        )
        return res
