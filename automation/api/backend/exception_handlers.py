"""
Глобальные обработчики исключений для стандартизации формата ошибок API.

Все ошибки возвращаются в едином формате:
{
    "error_code": "VALIDATION_ERROR",
    "message": "Краткое описание ошибки",
    "details": { ... }  // опционально
}
"""
from rest_framework.views import exception_handler
from rest_framework import status
from django.db import IntegrityError
from django.http import JsonResponse


def custom_exception_handler(exc, context):
    """
    Перехватывает стандартные DRF-исключения и форматирует их
    в единый JSON-формат для фронтенда.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Маппинг HTTP-кодов на читаемые error_code
        error_code_map = {
            400: 'BAD_REQUEST',
            401: 'UNAUTHORIZED',
            403: 'FORBIDDEN',
            404: 'NOT_FOUND',
            405: 'METHOD_NOT_ALLOWED',
            422: 'VALIDATION_ERROR',
        }

        status_code = response.status_code
        error_code = error_code_map.get(status_code, 'ERROR')

        # Извлекаем сообщение в зависимости от структуры ответа
        original_data = response.data

        if isinstance(original_data, dict):
            # Стандартные ошибки валидации DRF
            message = original_data.get('detail', 'Ошибка обработки запроса.')
            if message == 'Ошибка обработки запроса.' and original_data:
                # Это скорее всего ошибки полей — оставляем details
                message = 'Ошибка валидации данных.'
                details = original_data
            else:
                details = None
        elif isinstance(original_data, list):
            message = original_data[0] if original_data else 'Ошибка обработки запроса.'
            details = original_data
        else:
            message = str(original_data)
            details = None

        response.data = {
            'error_code': error_code,
            'message': str(message),
        }
        if details:
            response.data['details'] = details

    return response


def handle_integrity_error(request, exception):
    """
    Перехват IntegrityError на уровне Django middleware.
    Используется если ошибка проскочила мимо DRF-валидаторов
    (например, unique constraint на уровне БД).
    """
    return JsonResponse(
        {
            'error_code': 'INTEGRITY_ERROR',
            'message': 'Нарушение ограничения целостности базы данных.',
            'details': str(exception),
        },
        status=400,
    )
