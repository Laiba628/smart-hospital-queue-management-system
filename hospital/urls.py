from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    # =====================================================
    # ADMIN PANEL
    # =====================================================

    path("admin/", admin.site.urls),


    # =====================================================
    # QUEUE MANAGEMENT APP
    # =====================================================

    path(
        "",
        include("queue_management.urls")
    ),
]


# =========================================================
# MEDIA FILES
# Doctor profile pictures uploaded from Admin Panel
# =========================================================

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )