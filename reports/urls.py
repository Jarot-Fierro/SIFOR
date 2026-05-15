from django.urls import path

from . import views

urlpatterns = [
    # MANTENEDORES
    path('export/form/<str:form_code>', views.export_form, name='export_form'),


]
