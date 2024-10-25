from django.contrib.auth.models import User

# Filtrar y eliminar los usuarios con correos electrónicos que siguen el patrón example.com
User.objects.filter(email__endswith='@example.com').delete()

print("Usuarios eliminados.")

