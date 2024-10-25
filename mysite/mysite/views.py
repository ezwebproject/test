from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.forms import modelformset_factory
from .forms import UserUpdateForm
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
from django.forms import modelformset_factory # Asume que tienes un modelo de archivo llamado ProjectFile # Asegúrate de tener un formulario para archivos
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import get_language
from django.core.mail import send_mail
from django.conf import settings
from .models import ActivityLog

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
            elif user.groups.filter(name='Supervisor').exists():
                return redirect('supervisor')  # Redirect to /supervisor/
            else:
                return render(request, 'access_denied.html')
        else:
            # If authentication fails, return the login page with an error message
            return render(request, 'login.html', {'error': 'Invalid email, password or email not exist.'})

    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Guarda el usuario
            # Asigna al usuario al grupo "Client"
            client_group = Group.objects.get(name='Client')
            user.groups.add(client_group)
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')  # Redirige a la página de login después de registrarse
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})

def policy_terms_view(request):
    # Lógica para manejar el formulario de registro
    return render(request, 'policy_terms.html')



###########################################################################################################################################
@login_required
def client_view(request):
    # Definir el formset para los archivos de proyecto
    ProjectFileFormSet = modelformset_factory(ClientProjectFile, form=ClientProjectFileForm, extra=3)

    project_form = ClientProjectForm()  # El formulario para crear el proyecto
    formset = ProjectFileFormSet(queryset=ClientProjectFile.objects.none())  # Crear el formset para los archivos

    # Obtener los proyectos del usuario logueado
    projects = ClientProject.objects.filter(user=request.user)  # Filtrar proyectos del usuario logueado

    # Obtener los archivos asociados a los proyectos del usuario logueado
    client_files = ClientProjectFile.objects.filter(project__user=request.user)



    for file in client_files:
        file.basename = file.file.name.split('/')[-1]  # Dividir por '/' y obtener el último elemento

 # Verificar si es la primera vez que el usuario ha ingresado
    if 'welcome_shown' not in request.session:
        show_welcome_modal = True
        request.session['welcome_shown'] = True  # Marcar como mostrado
    else:
        show_welcome_modal = False

    
    return render(request, 'client.html', {
        'project_form': project_form,
        'formset': formset,
        'projects': projects,
        'client_files': client_files,  # Pasamos los archivos del cliente al template
        'LANGUAGE_CODE': get_language(),
        'show_welcome_modal': show_welcome_modal  # Pasar la variable al template
    })



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
            # Validar cada archivo en el formset
            for form in formset:
                if form.cleaned_data:
                    file = form.cleaned_data['file']

                    # Verificar si el nombre del archivo excede los 100 caracteres
                    if len(file.name) > 100:
                        form.add_error('file', 'El nombre del archivo es demasiado largo. Por favor, usa un nombre más corto.')

            # Si hay errores en el formset, no continuar
            if formset.non_form_errors() or any(form.errors for form in formset):
                return render(request, 'create_project.html', {
                    'project_form': project_form,
                    'formset': formset,
                })

            # Guardamos el proyecto sin hacer commit aún, para poder asignar el usuario
            project = project_form.save(commit=False)
            project.user = request.user  # Asignamos el usuario autenticado al proyecto
            project.save()  # Guardamos el proyecto

            ActivityLog.objects.create(user=request.user, action=f"Creo un nuevo proyecto: {project.title}")

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
    ActivityLog.objects.create(user=request.user, action=f"Elimino el proyecto {project.title}")
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
def client_project_file_delete_filesSection(request, file_id):
 # Obtener el archivo del proyecto, asegurando que pertenece al cliente logueado
    project_file = get_object_or_404(ClientProjectFile, id=file_id, project__user=request.user)
    
    # Eliminar el archivo
    project_file.delete()

    # Verificar si la solicitud es AJAX y devolver una respuesta JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    # Redirigir en caso de que no sea una solicitud AJAX
    return HttpResponseRedirect(reverse('client_view') + '#filesSection')
    
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


#########################################################################################################################################

def is_admin(user):
    return user.groups.filter(name__in=['Admin', 'Supervisor']).exists()


@login_required
def admin_view(request):
    # Verificación si el usuario es admin
    if not is_admin(request.user):
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

    # Cargar todos los proyectos de los clientes
    projects = ClientProject.objects.all()
    # Obtener todos los usuarios que están en el grupo "Client"
    clients_group = Group.objects.get(name='Client')
    clients = User.objects.filter(groups=clients_group)
    client_files = ClientProjectFile.objects.all()
    supervisors_group = Group.objects.get(name='Supervisor')
    admin_group = Group.objects.get(name='Admin')
    
    # Excluir el usuario logueado de la lista
    supervisors = User.objects.filter(groups__in=[supervisors_group, admin_group]).exclude(id=request.user.id)
    logs = ActivityLog.objects.all().order_by('-timestamp')
    user = request.user

    # Determinar el rol del usuario
    if user.groups.filter(name='Admin').exists():
        role = 'Admin'
    elif user.groups.filter(name='Supervisor').exists():
        role = 'Supervisor'
    else:
        role = 'Client'
        
    if request.method == 'POST':
        # Aquí podrías manejar la creación de proyectos o algún otro formulario
        pass

    return render(request, 'admin.html', {
        'projects': projects,
        'clients': clients,
        'client_files': client_files,
        'supervisors': supervisors,
        'user': user,
        'role': role,
        'logs': logs,
        'LANGUAGE_CODE': get_language(),
    })


    
@login_required
def admin_create_project(request):
    clients = User.objects.filter(groups__name='Clients')  # Obtener todos los clientes

    if request.method == 'POST':
        # Usar el formulario correspondiente para ClientProject
        form = ClientProjectForm(request.POST)  
        files = request.FILES.getlist('files')  # Obtener los archivos

        if form.is_valid():
            # Guardar el proyecto en ClientProject
            project = form.save(commit=False)
            project.user = User.objects.get(id=request.POST['client_id'])  # Asigna el cliente seleccionado
            project.save()  # Guarda el proyecto en el modelo ClientProject
            full_name = f"{project.user.first_name} {project.user.last_name}"
            ActivityLog.objects.create(user=request.user, action=f"Creo un nuevo proyecto para el cliente {full_name}")
            # Guardar los archivos relacionados al proyecto
            for file in files:
                ClientProjectFile.objects.create(project=project, file=file)

            # Redirigir a la lista de proyectos después de la creación
            return redirect('admin')

    return redirect('admin')



@login_required
def view_project_files(request, project_id):
    # Obtener el proyecto y los archivos asociados
    project = get_object_or_404(ClientProject, id=project_id)
    files = ClientProjectFile.objects.filter(project=project)
    
    return render(request, 'view_project_files.html', {'project': project, 'files': files})


@login_required
def upload_project_files(request, project_id):
    project = get_object_or_404(ClientProject, id=project_id)

    if request.method == 'POST':
        form = ClientProjectFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save(commit=False)
            file_instance.project = project
            file_instance.save()
            return redirect('view_project_files', project_id=project.id)
    
    form = ClientProjectFileForm()
    return render(request, 'upload_project_files.html', {'form': form, 'project': project})


@login_required
def download_project_files(request, project_id):
    project = get_object_or_404(ClientProject, id=project_id)
    files = ClientProjectFile.objects.filter(project=project)

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
def delete_project(request, project_id):
    project = get_object_or_404(ClientProject, id=project_id)
    projectname = ClientProject.objects.get(id=project_id)
    project_name = project.title
    user = get_object_or_404(User, id=project.user_id)
    full_name = f"{user.first_name} {user.last_name}"
    project.delete()
    ActivityLog.objects.create(user=request.user, action=f"Elimino el proyecto {project_name} del cliente {full_name}")
    return redirect('admin_view')

@login_required
def project_upload_file(request, project_id):
    project = get_object_or_404(ClientProject, id=project_id)

    if request.method == 'POST':
        form = ClientProjectFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save(commit=False)
            file_instance.project = project
            file_instance.save()
            return redirect('admin_view')  # Redirigir a la vista principal del administrador

    return redirect('admin_view')  # Si no es POST, redirigir al dashboard del administrador


@login_required
def admin_client_project_file_delete(request, file_id):
    # Obtener el archivo del proyecto sin verificar el usuario, ya que es el administrador
    project_file = get_object_or_404(ClientProjectFile, id=file_id)
    
    # Eliminar el archivo
    project_file.delete()
    
    # Redirigir a la vista de administración de proyectos
    return redirect(reverse('admin'))


@login_required
def admin_project_upload_files(request, project_id):
    project = get_object_or_404(ClientProject, id=project_id)

    if request.method == 'POST':
        form = ClientProjectFileForm(request.POST, request.FILES)  # Asegúrate de incluir request.FILES
        if form.is_valid():
            file_instance = form.save(commit=False)
            file_instance.project = project  # Asigna el proyecto actual
            file_instance.save()
            return redirect('admin')  # Redirigir después de subir los archivos
        else:
            print("Form errors:", form.errors)  # Imprime los errores del formulario para depurar

    return redirect('admin')


@login_required
def admin_files_section_view(request):
    # Aquí puedes filtrar o agregar lógica para los archivos que solo el admin puede ver
    client_files = ClientProjectFile.objects.all()  # O filtrados según sea necesario
    context = {
        'client_files': client_files,
    }
    return render(request, 'admin.html', context)

@login_required
def admin_project_file_delete_filesSection(request, file_id):
    file = get_object_or_404(ClientProjectFile, id=file_id)
    file.delete()
    return redirect('/admin/#filesSection')  # Redirigir a la sección de archivos


@login_required
def delete_user(request, user_id):
    # Obtener el usuario que se va a eliminar
    user = get_object_or_404(User, id=user_id)
    full_name = f"{user.first_name} {user.last_name}"
    # Eliminar el usuario
    user.delete()
    ActivityLog.objects.create(user=request.user, action=f"Elimino al cliente {full_name}")
    # Redirigir de vuelta a la página de clientes
    return redirect('/admin/#ClientsSection')


@login_required
def delete_supervisor(request, supervisor_id):
    supervisor = get_object_or_404(User, id=supervisor_id)
    full_name = f"{supervisor.first_name} {supervisor.last_name}"
    ActivityLog.objects.create(user=request.user, action=f"Elimino al miembro {full_name}")
    supervisor.delete()
    return redirect('/admin/#supervisorSection')


@login_required
def add_supervisor(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        group_name = request.POST['group']  # 'admin' o 'supervisor'
        ActivityLog.objects.create(user=request.user, action=f"Creo un nuevo miembro {name}")
         # Enviar el correo electrónico con el enlace
        subject = 'Invitacion a la plataforma JRH Architects'
        message = f'Hola {name},\n\nHas sido invitado a colaborar y gestionar los archivos de los clientes de nuestra compania JRH Architects.\n\nPor favor, haz clic en el siguiente enlace y accede a tu cuenta para comenzar:\n\nUsername: {email}\nPassword: {password}\n\nhttps://ezwebproject.pythonanywhere.com/\n\nSaludos cordiales,\nJRH Architects'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]
        send_mail(subject, message, from_email, recipient_list)

        # Crear el usuario
        user = User.objects.create_user(
            username=email,  # Usa el email como username
            email=email,
            password=password,
            first_name=name.split()[0],
            last_name=" ".join(name.split()[1:])

        )

        # Asignar el usuario al grupo correspondiente
        group = Group.objects.get(name=group_name.capitalize())
        user.groups.add(group)
        


        return redirect('/admin/#supervisorSection')

    return render(request, 'admin.html')  # Asegúrate de que redirija correctamente después de añadir el supervisor.

@login_required
def change_group(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        new_group_name = request.POST['group']  # 'admin' o 'supervisor'
        full_name = f"{user.first_name} {user.last_name}"
        ActivityLog.objects.create(user=request.user, action=f"Cambio el rol de miembro {full_name}")

        # Eliminar al usuario de sus grupos actuales
        user.groups.clear()

        # Asignar el usuario al nuevo grupo
        new_group = Group.objects.get(name=new_group_name.capitalize())
        user.groups.add(new_group)
        
    return redirect('/admin/#supervisorSection')


@login_required
def add_client(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')

        # Enviar el correo electrónico con el enlace
        subject = 'Invitacion a la plataforma JRH Architects'
        message = f'Hola {name},\n\nHas sido invitado a registrarte y gestionar los archivos de tu proyecto en nuestra plataforma.\n\nPor favor, haz clic en el siguiente enlace para completar tu registro y comenzar a subir archivos:\n\nhttps://ezwebproject.pythonanywhere.com/\n\nSaludos cordiales,\nJRH Architects'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        send_mail(subject, message, from_email, recipient_list)

        # Registrar la actividad
        ActivityLog.objects.create(user=request.user, action=f"Invitó a un nuevo cliente: {name} ({email})")

        # Verificar si el usuario es Admin o Supervisor y redirigir en consecuencia
        if request.user.groups.filter(name='Admin').exists():
            return redirect('/admin/#ClientsSection')
        elif request.user.groups.filter(name='Supervisor').exists():
            return redirect('/supervisor/#ClientsSection')
        else:
            return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
    
    return render(request, 'admin.html')  # Puedes ajustar el template si es necesario

def is_admin(user):
    # Verificar si el usuario está en el grupo 'Admin' únicamente
    return user.groups.filter(name='Admin').exists()



def is_supervisor(user):
    # Verificar si el usuario está en el grupo 'Supervisor'
    return user.groups.filter(name='Supervisor').exists()

@login_required
def supervisor_view(request):
    # Verificación si el usuario es supervisor
    if not is_supervisor(request.user):
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

    # Cargar todos los proyectos de los clientes
    projects = ClientProject.objects.all()
    clients_group = Group.objects.get(name='Client')
    clients = User.objects.filter(groups=clients_group)
    client_files = ClientProjectFile.objects.all()
    supervisors_group = Group.objects.get(name='Supervisor')
    admin_group = Group.objects.get(name='Admin')
    
    supervisors = User.objects.filter(groups__in=[supervisors_group, admin_group]).exclude(id=request.user.id)
    logs = ActivityLog.objects.all().order_by('-timestamp')
    user = request.user

    if user.groups.filter(name='Admin').exists():
        role = 'Admin'
    elif user.groups.filter(name='Supervisor').exists():
        role = 'Supervisor'
    else:
        role = 'Client'
        
    if request.method == 'POST':
        # Aquí podrías manejar la creación de proyectos o algún otro formulario
        pass

    return render(request, 'supervisor.html', {
        'projects': projects,
        'clients': clients,
        'client_files': client_files,
        'supervisors': supervisors,
        'user': user,
        'role': role,
        'logs': logs,
        'LANGUAGE_CODE': get_language(),
    })



########################################################################################################################################################


def error_404_view(request, exception):
    return render(request, 'errors/error.html', {
        'message': 'Ha ocurrido un error, favor de intentarlo nuevamente. Si el error persiste, intente más tarde.'
    }, status=404)

def error_500_view(request):
    return render(request, 'errors/error.html', {
        'message': 'Ha ocurrido un error, favor de intentarlo nuevamente. Si el error persiste, intente más tarde.'
    }, status=500)

def error_403_view(request, exception):
    return render(request, 'errors/error.html', {
        'message': 'No tienes permiso para acceder a esta página.'
    }, status=403)

def error_400_view(request, exception):
    return render(request, 'errors/error.html', {
        'message': 'Solicitud incorrecta, por favor inténtalo de nuevo.'
    }, status=400)
