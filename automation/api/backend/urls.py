from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Импортируем наши ViewSets
from .views import PartViewSet, PartCategoryViewSet, BomItemViewSet, StockItemViewSet

# Используем DefaultRouter для автоматической генерации стандартных REST маршрутов
router = DefaultRouter()

# Важно: Порядок регистрации имеет значение. Сначала регистрируем вложенные/специфичные роуты.
# Эндпоинт для категорий: /api/part/category/
router.register(r'category', PartCategoryViewSet, basename='partcategory')

# Эндпоинт для BOM: /api/part/bom/
router.register(r'bom', BomItemViewSet, basename='bomitem')

# Эндпоинт для складских остатков: /api/part/stock/
router.register(r'stock', StockItemViewSet, basename='stockitem')

# Эндпоинт для деталей: /api/part/
router.register(r'', PartViewSet, basename='part')

app_name = 'part'

urlpatterns = [
    # Подключаем все автоматически сгенерированные маршруты роутера
    path('', include(router.urls)),
    
    # ------------------------------------------------------------------------
    # OpenAPI / Swagger Schema - Требование п. 2.1
    # ------------------------------------------------------------------------
    
    # Генерация сырого OpenAPI 3.0 schema файла (.yaml / .json)
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Интерактивная документация Swagger UI
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='part:schema'), name='swagger-ui'),
    
    # Интерактивная документация ReDoc
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='part:schema'), name='redoc'),
]
