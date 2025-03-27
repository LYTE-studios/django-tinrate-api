from rest_framework import permissions

class ReadOnlyOrAuthenticatedEdit(permissions.BasePermission):
    """
    Custom permission:
    - Allow unauthenticated users to read (GET).
    - Only authenticated users can create, update, or delete.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True  # Allow read access to anyone
        return request.user and request.user.is_authenticated  # Modify only if authenticated

