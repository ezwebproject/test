from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.forms import modelformset_factory
from .forms import ProjectForm, ProjectFileForm, UserUpdateForm
from .models import Project, ProjectFile
from django.contrib import messages  
from django.http import JsonResponse
import zipfile
import os
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from .forms import ClientProjectForm
from django.forms import modelformset_factory
from django.forms import modelformset_factory
from .models import ClientProjectFile  # Importa el modelo si aún no lo tienes
from .forms import ClientProjectFileForm  # Asegúrate de que este formulario también esté definido
from .models import ClientProject
from django.forms import modelformset_factory
from .models import ProjectFile  # Asume que tienes un modelo de archivo llamado ProjectFile
from .forms import ProjectFileForm  # Asegúrate de tener un formulario para archivos





def login_view(request):
    if request.method == 'POST':
        # Get user credentials
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Log the user in
            login(request, user)

            # Check the user's group and redirect based on their role
            if user.groups.filter(name='Admin').exists():
                return redirect('admin')  # Redirect to /admin/
            elif user.groups.filter(name='Client').exists():
                return redirect('client')  # Redirect to /client/
            else:
                return render(request, 'access_denied.html')
        else:
            # If authentication fails, return the login page with an error message
            return render(request, 'login.html', {'error': 'Invalid email or password.'})

    return render(request, 'login.html')

@login_required  
def admin_dashboard_view(request):
    users = User.objects.all()  # Get all users
    return render(request, 'admin.html', {'users': users})


@login_required
def admin_view(request):
    # Obtenemos todos los usuarios junto con sus proyectos y archivos relacionados
    users = User.objects.prefetch_related('projects__files').all()
    
    # Obtenemos todos los archivos subidos por los usuarios
    files = ProjectFile.objects.all()  # Asegúrate de que ProjectFile es tu modelo para archivos

    return render(request, 'admin.html', {
        'users': users,
        'files': files  # Pasamos todos los archivos al contexto
    })

@login_required
def client_view(request):
    # Formset para manejar la subida de archivos
    files = ProjectFile.objects.all()  # Todos los archivos subidos
    projects = Project.objects.all()
    ProjectFileFormSet = modelformset_factory(ProjectFile, form=ProjectFileForm, extra=3)

    if request.method == 'POST':
        project_form = ProjectForm(request.POST)
        formset = ProjectFileFormSet(request.POST, request.FILES, queryset=ProjectFile.objects.none())

        if project_form.is_valid() and formset.is_valid():
            project = project_form.save()

            for form in formset.cleaned_data:
                if form:
                    file = form['file']
                    ProjectFile.objects.create(project=project, file=file)

            # Mensaje de éxito cuando el proyecto es creado correctamente
            messages.success(request, 'Project created successfully!')
            return redirect('client')

        else:
            # Mensaje de error si hay algún problema con el formulario
            messages.error(request, 'There was an error creating the project. Please try again.')
    else:
        project_form = ProjectForm()
        formset = ProjectFileFormSet(queryset=ProjectFile.objects.none())

    return render(request, 'client.html', {
        'project_form': project_form,
        'formset': formset,
          'projects': projects,
          'files': files,
        # Otros datos que necesites pasar a la plantilla
    })

@login_required
def employee_view(request):
    return render(request, 'employee.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Save the new user
            user = form.save()

            # Get the "Client" group
            client_group = Group.objects.get(name='Client')

            # Add the user to the "Client" group
            user.groups.add(client_group)

            # Add a success message
            messages.success(request, 'Your account has been created successfully!')

            # Redirect to the login page
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})




@login_required
def create_project(request):
    ProjectFileFormSet = modelformset_factory(ProjectFile, form=ProjectFileForm, extra=3)

    if request.method == 'POST':
        project_form = ProjectForm(request.POST)
        formset = ProjectFileFormSet(request.POST, request.FILES, queryset=ProjectFile.objects.none())

        # Debugging: print the current user to see if it's None or valid
        print("Is user authenticated:", request.user.is_authenticated)  # Should print True if user is logged in
        print("Current user:", request.user)  # Should print the user object

        if project_form.is_valid() and formset.is_valid():
            project = project_form.save(commit=False)
            project.user = request.user  # Assign the current logged-in user to the project

            print("Assigned user to project:", project.user)  # Debugging: print the user assigned to the project

            project.save()  # Save the project with the assigned user

            # Save the files
            for form in formset.cleaned_data:
                if form:
                    file = form['file']
                    ProjectFile.objects.create(project=project, file=file)

            return redirect('client')

    else:
        project_form = ProjectForm()
        formset = ProjectFileFormSet(queryset=ProjectFile.objects.none())

    return render(request, 'create_project.html', {
        'project_form': project_form,
        'formset': formset,
    })

@login_required
def delete_file(request, file_id):
    # Recuperamos el archivo por su ID
    file = get_object_or_404(ProjectFile, id=file_id)
    project_id = file.project.id  # Guardamos el ID del proyecto para referencia
    file.delete()  # Eliminamos el archivo de la base de datos

    # Devolvemos una respuesta JSON después de eliminar el archivo
    return JsonResponse({'success': True})

@login_required
def add_file_to_project(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)
        
        if 'file' in request.FILES:
            file = request.FILES['file']
            project_file = ProjectFile.objects.create(project=project, file=file)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
def delete_project(request, project_id):
    if request.method == 'POST':
        try:
            project = Project.objects.get(id=project_id)
            project.delete()
            return JsonResponse({'success': True})  # Respuesta en caso de éxito
        except Project.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def account_settings(request):
    user = request.user
    return render(request, 'account_settings.html', {'user': user})

@login_required
def account_settings(request):
    user = request.user

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()  # Guardamos los cambios en el usuario
            return redirect('account_settings')  # Redirige para evitar el reenvío del formulario
    else:
        form = UserUpdateForm(instance=user)  # Inicializamos el formulario con los datos actuales del usuario

    return render(request, 'account_settings.html', {'form': form})

@login_required    
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()  # Eliminar el usuario
    return redirect('/admin/#ClientsSection')  # Redirige a la lista de clientes después de eliminar

@login_required
def admin_clients_projects(request):
    clients = User.objects.all()  # Obtener todos los clientes
    client_id = request.GET.get('client_id')  # Obtener el cliente seleccionado
    projects = None
    selected_client = None
    
    if client_id:
        selected_client = get_object_or_404(User, id=client_id)
        projects = Project.objects.filter(client=selected_client)  # Filtra proyectos por cliente
    
    return render(request, 'projects_section.html', {'clients': clients, 'projects': projects, 'selected_client': selected_client})



def download_all_files(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    files = project.files.all()

    # Crear el archivo ZIP en memoria
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{project.title}_files.zip"'

    with zipfile.ZipFile(response, 'w') as zipf:
        for file in files:
            file_path = file.file.path
            file_name = os.path.basename(file_path)
            zipf.write(file_path, file_name)

    return response



@login_required
def files_view(request):
    files = ProjectFile.objects.all()  # Get all files
    return render(request, 'admin.html', {'files': files})

@user_passes_test(lambda u: u.is_staff)  # Solo los usuarios con permisos de administrador
@csrf_exempt
def delete_file_admin(request, file_id):
  if request.method == 'POST':
        file = get_object_or_404(ProjectFile, id=file_id)
        file.delete()  # Eliminar el archivo del modelo
        # Redirigir a la página de admin o donde quieras después de eliminar el archivo
        return redirect('admin')  # Ajusta la redirección a tu URL correcta

def get_projects(request):
    projects = Project.objects.select_related('user').all()
    projects_data = [
        {
            'title': project.title,
            'description': project.description,
            'created_at': project.created_at.strftime("%B %d, %Y"),
            'client_name': f"{project.user.first_name} {project.user.last_name}" if project.user else "Unknown Client",
            'files': [
                {'name': file.file.name, 'url': file.file.url} for file in project.files.all()
            ]
        }
        for project in projects
    ]
    return JsonResponse({'projects': projects_data})


def upload_file(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']
        ProjectFile.objects.create(
            project=project,
            file=uploaded_file
        )
        return redirect('admin')

    return HttpResponse("Error al subir archivo", status=400)

###########################################################################################################################################

@login_required
def client_project_list(request):
    projects = ClientProject.objects.filter(user=request.user)  # Solo los proyectos del usuario logueado
    return render(request, 'client/project_list.html', {'projects': projects})


@login_required
def client_project_create(request):
    # Creamos el formset para los archivos relacionados al proyecto
    ProjectFileFormSet = modelformset_factory(ClientProjectFile, form=ClientProjectFileForm, extra=3)
    
    if request.method == 'POST':
        # Capturar los datos del formulario y los archivos
        project_form = ClientProjectForm(request.POST)
        formset = ProjectFileFormSet(request.POST, request.FILES, queryset=ClientProjectFile.objects.none())

        # Comprobamos si el formulario y el formset son válidos
        if project_form.is_valid() and formset.is_valid():
            # Guardamos el proyecto sin hacer commit aún, para poder asignar el usuario
            project = project_form.save(commit=False)
            project.user = request.user  # Asignamos el usuario autenticado al proyecto
            project.save()  # Guardamos el proyecto

            # Guardamos los archivos
            for form in formset.cleaned_data:
                if form:
                    file = form['file']
                    # Guardar el archivo asociado al proyecto
                    ClientProjectFile.objects.create(project=project, file=file)

            # Redirigimos a la página de proyectos del usuario
            return redirect('client_view')

    else:
        # Si es un GET, mostrar los formularios vacíos
        project_form = ClientProjectForm()
        formset = ProjectFileFormSet(queryset=ClientProjectFile.objects.none())

    return render(request, 'create_project.html', {
        'project_form': project_form,
        'formset': formset,
    })

@login_required
def client_project_delete(request, project_id):
    project = get_object_or_404(ClientProject, id=project_id, user=request.user)
    project.delete()
    return redirect('client_view')


@login_required
def client_project_upload_files(request, project_id):
    project = get_object_or_404(ClientProject, id=project_id, user=request.user)  # Verificar que el proyecto pertenezca al usuario logueado

    if request.method == 'POST':
        form = ClientProjectFileForm(request.POST, request.FILES)  # Asegúrate de incluir request.FILES
        if form.is_valid():
            file_instance = form.save(commit=False)
            file_instance.project = project  # Asigna el proyecto actual
            file_instance.save()

            # Responder con JSON si la petición es AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'file_name': file_instance.file.name})

            return redirect('client')  # En caso de que no sea AJAX, redirigir

        # Agrega esta parte para imprimir los errores del formulario
        else:
            print("Form errors:", form.errors)  # Imprime los errores del formulario
            return JsonResponse({'success': False, 'error': 'Invalid form submission', 'form_errors': form.errors})

    # Si no es un POST, retornar un error
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def client_project_file_delete(request, file_id):
    # Obtener el archivo del proyecto, asegurando que pertenece al cliente logueado
    project_file = get_object_or_404(ClientProjectFile, id=file_id, project__user=request.user)
    project_file.delete()
    return redirect('client_view')


@login_required
def client_view(request):
    # Definir el formset para los archivos de proyecto
    ProjectFileFormSet = modelformset_factory(ClientProjectFile, form=ClientProjectFileForm, extra=3)

    project_form = ClientProjectForm()  # El formulario para crear el proyecto
    formset = ProjectFileFormSet(queryset=ClientProjectFile.objects.none())  # Crear el formset para los archivos

    projects = ClientProject.objects.filter(user=request.user)  # Filtrar proyectos del usuario logueado

    return render(request, 'client.html', {
        'project_form': project_form,
        'formset': formset,
        'projects': projects,
    })

@login_required
def client_download_project_files(request, project_id):
    project = get_object_or_404(ClientProject, id=project_id, user=request.user)
    files = ClientProjectFile.objects.filter(project=project)

    # Crear un objeto en memoria para el archivo zip
    zip_filename = f"{project.title}_files.zip"
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={zip_filename}'

    with zipfile.ZipFile(response, 'w') as zip_file:
        for project_file in files:
            file_path = project_file.file.path
            file_name = os.path.basename(file_path)
            zip_file.write(file_path, file_name)

    return response

@login_required
def client_files_view(request):
    # Formulario para crear proyectos y formset para subir archivos
    ProjectFileFormSet = modelformset_factory(ClientProjectFile, form=ClientProjectFileForm, extra=3)

    project_form = ClientProjectForm()  # El formulario para crear el proyecto
    formset = ProjectFileFormSet(queryset=ClientProjectFile.objects.none())  # Crear el formset para los archivos

    # Obtener los proyectos del usuario logueado
    projects = ClientProject.objects.filter(user=request.user)

    # Obtener los archivos asociados a los proyectos del cliente
    client_files = ClientProjectFile.objects.filter(project__user=request.user)

    return render(request, 'client.html', {
        'project_form': project_form,
        'formset': formset,
        'projects': projects,
        'client_files': client_files,  # Pasamos los archivos del cliente al template
    })

