
from rest_framework import generics
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Role, User
from .permissions import IsAdminRole
from .serializers import CustomTokenObtainPairSerializer, UserSerializer


class LoginView(TokenObtainPairView):
    """POST username + password -> access, refresh, user."""

    serializer_class = CustomTokenObtainPairSerializer


class MeView(generics.RetrieveAPIView):
    """Returns the currently logged in user."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class EmployeeListView(generics.ListAPIView):
    """Admin only: list active sales employees (used to pick an assignee)."""

    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
    queryset = User.objects.filter(role=Role.SALES, is_active=True).order_by("id")