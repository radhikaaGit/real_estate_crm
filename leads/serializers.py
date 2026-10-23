from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from accounts.models import Role, User

from .models import Lead

LEAD_FIELDS = (
    "id",
    "customer_name",
    "phone_number",
    "email",
    "interested_property",
    "budget",
    "lead_source",
    "status",
    "lost_reason",
    "assigned_to",
    "assigned_to_name",
    "created_by",
    "created_at",
    "updated_at",
)


def active_sales_users():
    return User.objects.filter(role=Role.SALES, is_active=True)


class LeadBaseSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = LEAD_FIELDS

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.username if obj.assigned_to else None

    def validate(self, attrs):
        """Business rule: a Lost lead must include a reason."""
        current_status = self.instance.status if self.instance else Lead.Status.NEW
        current_reason = self.instance.lost_reason if self.instance else ""

        status = attrs.get("status", current_status)
        reason = (attrs.get("lost_reason", current_reason) or "").strip()

        if status == Lead.Status.LOST:
            if not reason:
                raise serializers.ValidationError(
                    {"lost_reason": "A reason is required when a lead is marked as Lost."}
                )
            attrs["lost_reason"] = reason
        else:
            # Reason only makes sense for Lost leads.
            attrs["lost_reason"] = ""
        return attrs


class LeadAdminSerializer(LeadBaseSerializer):
    """Admin can write everything except system-managed fields."""

    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=active_sales_users(),
        required=False,
        allow_null=True,
        error_messages={"does_not_exist": "Employee not found or is not an active sales employee."},
    )

    class Meta(LeadBaseSerializer.Meta):
        read_only_fields = ("id", "created_by", "created_at", "updated_at")


class LeadEmployeeSerializer(LeadBaseSerializer):
    """
    Sales employee can edit lead details and status only.
    `assigned_to` and other system fields are read-only, and any attempt
    to change ownership is rejected with 403 instead of being silently ignored.
    """

    class Meta(LeadBaseSerializer.Meta):
        read_only_fields = (
            "id",
            "assigned_to",
            "created_by",
            "created_at",
            "updated_at",
        )

    def to_internal_value(self, data):
        if hasattr(data, "get") and self.instance is not None:
            for field in ("assigned_to", "created_by"):
                if field in data and str(data.get(field)) != str(getattr(self.instance, f"{field}_id")):
                    raise PermissionDenied(
                        "Only admins can assign leads or change protected fields."
                        if field == "assigned_to"
                        else f"You are not allowed to modify '{field}'."
                    )
        return super().to_internal_value(data)


class AssignLeadSerializer(serializers.Serializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=active_sales_users(),
        error_messages={
            "does_not_exist": "Employee not found or is not an active sales employee.",
            "required": "assigned_to (employee id) is required.",
            "null": "assigned_to cannot be null.",
        },
    )