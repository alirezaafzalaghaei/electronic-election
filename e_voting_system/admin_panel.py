from django.contrib.admin import AdminSite
from django.views.decorators.cache import never_cache


class MyAdminSite(AdminSite):
    @never_cache
    def index(self, request, extra_context=None):
        pass

admin_site = MyAdminSite()