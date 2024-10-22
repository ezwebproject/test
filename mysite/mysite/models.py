from django.db import models
from django.contrib.auth.models import User
from django import forms

class Project(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')  # Agregar related_name

    def __str__(self):
        return self.title


class ProjectFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='project_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} for {self.project.title}"




class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description']  # Excluye el campo 'user'


class ProjectAdmin(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ProjectFileAdmin(models.Model):
    project = models.ForeignKey(ProjectAdmin, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='project_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

#########################################################################################################################

class ClientProject(models.Model):
    title = models.CharField(max_length=255)  # Título del proyecto
    description = models.TextField(blank=True, null=True)  # Descripción del proyecto
    created_at = models.DateTimeField(auto_now_add=True)  # Fecha de creación automática
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_projects')  # Relación con el cliente que crea el proyecto

    def __str__(self):
        return self.title


class ClientProjectFile(models.Model):
    project = models.ForeignKey(ClientProject, on_delete=models.CASCADE, related_name='client_files')  # Relación con el proyecto del cliente
    file = models.FileField(upload_to='client_project_files/')  # Almacenamiento del archivo
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Fecha de subida automática

    def __str__(self):
        return f"{self.file.name} for {self.project.title}"

###########################################################################################################################
# Modelo para los proyectos gestionados por el administrador
class AdminProject(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_projects')

    def __str__(self):
        return f"{self.title} (Assigned to: {self.assigned_client.username})"

# Modelo para los archivos asociados a los proyectos gestionados por el administrador
class AdminProjectFile(models.Model):
    project = models.ForeignKey(AdminProject, on_delete=models.CASCADE, related_name='admin_files')
    file = models.FileField(upload_to='admin_project_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} (Project: {self.project.title})"
