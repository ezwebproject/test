from django.db import models
from django.contrib.auth.models import User
from django import forms

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"


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


