from rest_framework.permissions import BasePermission

class IsAuthenticatedWithSessionOrJWT(BasePermission):
    """
    Allows access if the user is authenticated using either Session or JWT authentication.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if request.user and request.user.is_authenticated:
            return True

        # Alternatively, check for valid JWT tokens (if needed)
        if request.auth:  # JWT tokens are usually in request.auth
            return True

        return False
