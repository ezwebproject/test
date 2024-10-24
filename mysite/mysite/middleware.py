import logging
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseServerError

logger = logging.getLogger(__name__)

class GlobalExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Continuar con la ejecución normal si no hay errores
            response = self.get_response(request)
            return response
        except Exception as e:
            # Capturar cualquier error y registrar el problema en los logs
            logger.error(f"Error inesperado: {str(e)}")
            # Agregar un mensaje de error utilizando el sistema de mensajes de Django
            messages.error(request, "Ha ocurrido un error inesperado. Por favor, intenta nuevamente más tarde.")
            # Renderizar una plantilla genérica de error o simplemente devolver el mensaje
            return render(request, 'errors/error_message.html', status=500)
