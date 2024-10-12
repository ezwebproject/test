"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from mysite.views import client_project_create


urlpatterns = [
    path('', views.login_view, name='login'),  # Página de login en la raíz
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # Ruta para logout
    path('client/', views.client_view, name='client'),
    path('admin/', views.admin_view, name='admin'),
    path('employee/', views.employee_view, name='employee'),
    path('register/', views.register_view, name='register'),
    path('delete-file/<int:file_id>/', views.delete_file, name='delete_file'),
    path('project/<int:project_id>/add_file/', views.add_file_to_project, name='add_file_to_project'),
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('create_project/', views.create_project, name='create_project'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin/clients-projects/', views.admin_clients_projects, name='admin_clients_projects'),
    path('download_all_files/<int:project_id>/', views.download_all_files, name='download_all_files'),
    path('download_all_files/', views.download_all_files, name='download_all_files'),
    path('files/', views.files_view, name='files_view'),
    path('admin/delete-file/<int:file_id>/', views.delete_file_admin, name='delete_file_admin'),
    path('get-projects/', views.get_projects, name='get-projects'),
    path('project/<int:project_id>/upload/', views.upload_file, name='upload_file'),

##################################################################################################################

    # Listar los proyectos del cliente
    path('projects/', views.client_project_list, name='client_project_list'),

    # Crear un nuevo proyecto
    path('projects/create/', views.client_project_create, name='client_project_create'),

    # Subir archivos a un proyecto
    path('projects/<int:project_id>/upload/', views.client_project_upload_files, name='client_project_upload_files'),

    # Eliminar un proyecto
    path('projects/<int:project_id>/delete/', views.client_project_delete, name='client_project_delete'),

    # Eliminar un archivo de un proyecto
    path('projects/file/<int:file_id>/delete/', views.client_project_file_delete, name='client_project_file_delete'),


    path('client/', views.client_view, name='client_view'),

    # Ruta para descargar archivos de un proyecto
    path('client/projects/<int:project_id>/download/', views.client_download_project_files, name='client_download_project_files'),

    # Nueva URL para la vista de archivos
    path('client/files/', views.client_files_view, name='client_files'),  
   

    # This will display index.html on the root URL


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
