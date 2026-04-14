"""
Middleware для перехвата ошибок целостности БД (IntegrityError),
которые проскочили мимо DRF-валидаторов.

Гарантирует, что клиент никогда не увидит raw 500-ошибку
из-за нарушения unique constraint или foreign key.
"""
import json
from django.db import IntegrityError
from django.http import JsonResponse


class IntegrityErrorMiddleware:
    """
    Перехватывает django.db.IntegrityError и возвращает
    структурированный JSON-ответ со статусом 400 вместо 500.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, IntegrityError):
            return JsonResponse(
                {
                    'error_code': 'INTEGRITY_ERROR',
                    'message': 'Нарушение ограничения целостности базы данных.',
                    'details': str(exception),
                },
                status=400,
            )
        return None
