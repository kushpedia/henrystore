
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import custom_page_not_found, custom_server_error

urlpatterns = [
    path('admin/', admin.site.urls),
	path('', include('core.urls')),
    path('users/', include('userauths.urls')),
    path("useradmin/", include("useradmin.urls")),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('payments/', include('payments.urls')),
    path('corporate/', include('corporate.urls')),

]
handler404 = 'core.views.custom_page_not_found'
handler500 = 'core.views.custom_server_error'


if settings.DEBUG:
    urlpatterns +=  static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns +=  static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

