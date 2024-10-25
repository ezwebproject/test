import random
import os
from django.contrib.auth.models import User, Group
from mysite.models import ClientProject, ClientProjectFile  # Importa el modelo correcto para los archivos

# Datos de ejemplo para nombres y apellidos
first_names = ['Juan', 'Maria', 'Carlos', 'Sofia', 'Andres', 'Laura', 'Pedro', 'Marta', 'Luis', 'Ana']
last_names = ['Gonzalez', 'Rodriguez', 'Martinez', 'Perez', 'Sanchez', 'Diaz', 'Lopez', 'Ramirez', 'Cruz', 'Vargas']

# Cambiar el directorio de archivos a 'media/client_project_files'
project_files_directory = os.path.join('media', 'client_project_files')

# Asegurarse de que el directorio de archivos exista
if not os.path.exists(project_files_directory):
    os.makedirs(project_files_directory)

# Función para crear un usuario
def crear_usuario(i, client_group):
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    email = f"{first_name.lower()}{i}@example.com"
    username = email  # Asignar email como username
    password = f"password{i}"
    
    # Crear usuario
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password
    )
    
    # Añadir el usuario al grupo "Client"
    user.groups.add(client_group)

    return user, first_name, last_name

# Función para crear proyectos para un usuario
def crear_proyectos_para_usuario(user, first_name, last_name):
    for j in range(1, 4):
        project_title = f"Project {j} for {first_name} {last_name}"
        project_description = f"This is the description for {project_title}."
        
        # Crear el proyecto asociado al usuario
        project = ClientProject.objects.create(
            title=project_title,
            description=project_description,
            created_at=random.choice(['2023-10-01', '2023-11-05', '2023-12-15']),
            user=user  # Pasar el objeto `User` directamente
        )
        
        # Crear un archivo de texto para el proyecto en 'media/client_project_files'
        file_path = os.path.join(project_files_directory, f"{project_title.replace(' ', '_')}.txt")
        with open(file_path, 'w') as f:
            f.write(f"Title: {project_title}\n")
            f.write(f"Description: {project_description}\n")
            f.write(f"User: {first_name} {last_name} (Email: {user.email})\n")
            f.write(f"Created at: {project.created_at}\n")
        
        # Registrar el archivo en la base de datos en el modelo `ClientProjectFile`
        project_file = ClientProjectFile.objects.create(
            file=file_path,  # Guardamos la ruta del archivo
            project=project,  # Asociamos el archivo al proyecto correspondiente
            uploaded_at=random.choice(['2023-10-01', '2023-11-05', '2023-12-15'])  # Simular fecha de subida
        )

# Función principal para generar usuarios y proyectos
def generar_usuarios_y_proyectos():
    client_group = Group.objects.get(name='Client')

    # Generar 20 usuarios
    for i in range(1, 20):
        user, first_name, last_name = crear_usuario(i, client_group)
        crear_proyectos_para_usuario(user, first_name, last_name)
        print(f"Created user {user.username} and 3 projects with associated text files.")

# Ejecutar la función principal
generar_usuarios_y_proyectos()
