import re

from django.http import HttpResponseRedirect
from django.urls import reverse


class RoleBasedAccessMiddleware:
    FORM_USER_ALLOWED_PATHS = [
        re.compile(r"^/forms/visits$"),
        re.compile(r"^/form/[^/]+/viewform$"),
        re.compile(r"^/form/[^/]+/submit$"),
        re.compile(r"^/form/[^/]+/response/[^/]+/edit$"),
        re.compile(r"^/form/[^/]+/already-voted$"),
        re.compile(r"^/form/[^/]+/my-response$"),
        re.compile(r"^/logout$"),
        re.compile(r"^/403$"),
        re.compile(r"^/404$"),
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        user = request.user

        if user.is_authenticated and not user.is_superuser:
            if user.is_staff:
                if path.startswith("/admin/"):
                    return HttpResponseRedirect(reverse("403"))
            else:
                if not any(pattern.match(path) for pattern in self.FORM_USER_ALLOWED_PATHS):
                    return HttpResponseRedirect(reverse("403"))

        return self.get_response(request)
