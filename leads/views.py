from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminRole

from .filters import LeadFilter
from .models import Lead
from .permissions import IsAdminOrAssignedEmployee
from .serializers import (
    AssignLeadSerializer,
    LeadAdminSerializer,
    LeadEmployeeSerializer,
)


class LeadViewSet(viewsets.ModelViewSet):
    """
    list      GET    /api/leads/               admin: all | employee: own
    create    POST   /api/leads/               admin only
    retrieve  GET    /api/leads/{id}/          admin | assigned employee
    update    PUT    /api/leads/{id}/          admin | assigned employee
    partial   PATCH  /api/leads/{id}/          admin | assigned employee
    destroy   DELETE /api/leads/{id}/          admin only
    assign    POST   /api/leads/{id}/assign/   admin only
    """

    filterset_class = LeadFilter
    search_fields = ["customer_name", "email", "phone_number", "interested_property"]
    ordering_fields = ["created_at", "budget", "customer_name", "status"]
    ordering = ["-created_at"]

    # ---- queryset-level isolation: employees can only ever "see" their leads
    def get_queryset(self):
        queryset = Lead.objects.select_related("assigned_to", "created_by")
        user = self.request.user
        if user.is_admin_role:
            return queryset
        return queryset.filter(assigned_to=user)

    def get_serializer_class(self):
        if self.action == "assign":
            return AssignLeadSerializer
        if self.request.user.is_admin_role:
            return LeadAdminSerializer
        return LeadEmployeeSerializer

    # ---- role-level permissions per action
    def get_permissions(self):
        if self.action in ("create", "destroy", "assign"):
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated(), IsAdminOrAssignedEmployee()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        lead = self.get_object()
        serializer = AssignLeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lead.assigned_to = serializer.validated_data["assigned_to"]
        lead.save(update_fields=["assigned_to", "updated_at"])

        output = LeadAdminSerializer(lead, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_200_OK)