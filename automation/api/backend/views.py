from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Q

from .models import Part, PartCategory, BomItem, StockItem
from .serializers import (
    PartSerializer,
    PartCategorySerializer,
    PartCategoryTreeSerializer,
    BomItemSerializer,
    StockItemSerializer,
)


# ---------------------------------------------------------------------------
# Пагинация
# ---------------------------------------------------------------------------

class StandardPagination(PageNumberPagination):
    """
    Стандартная пагинация для всех эндпоинтов.
    Клиент может управлять размером страницы через query-параметр ?page_size=N.
    Жёсткий потолок — 100 записей для защиты от перегрузки БД.
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


# ---------------------------------------------------------------------------
# PartCategory ViewSet
# ---------------------------------------------------------------------------

class PartCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления категориями деталей (PartCategory).

    Поддерживает:
    - CRUD операции (GET / POST / PUT / PATCH / DELETE)
    - Фильтрацию по родительской категории (?parent=<id>)
    - Полнотекстовый поиск по названию (?search=<term>)
    - Сортировку (?ordering=name / -name)
    - Пагинацию (?page=1&page_size=25)
    - Кастомный action `root` для получения только корневых категорий
    - Кастомный action `tree` для получения полного дерева категорий
    """
    serializer_class = PartCategorySerializer
    pagination_class = StandardPagination

    # Чтение — всем, изменения — только авторизованным
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Бэкенды фильтрации, поиска и сортировки
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent']
    search_fields = ['name']
    ordering_fields = ['id', 'name']
    ordering = ['name']  # сортировка по умолчанию

    def get_queryset(self):
        """
        Оптимизированный queryset: аннотируем количество деталей в каждой
        категории на уровне БД, чтобы избежать N+1 запросов.
        """
        return PartCategory.objects.annotate(
            part_count=Count('parts')
        ).select_related('parent')

    # ------------------------------------------------------------------
    # Кастомный action: GET /api/part/category/root/
    # Возвращает только корневые категории (parent=None)
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='root')
    def root_categories(self, request):
        """Возвращает список корневых категорий (без родителя)."""
        queryset = self.get_queryset().filter(parent__isnull=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Кастомный action: GET /api/part/category/tree/
    # Возвращает полное дерево категорий (иерархическое представление)
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='tree')
    def category_tree(self, request):
        """
        Возвращает полное дерево категорий, начиная с корневых узлов.
        Использует легковесный PartCategoryTreeSerializer для быстрой навигации.
        """
        root_categories = PartCategory.objects.filter(
            parent__isnull=True
        ).prefetch_related('children')
        serializer = PartCategoryTreeSerializer(root_categories, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Part ViewSet
# ---------------------------------------------------------------------------

class PartViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления деталями (Part).

    Поддерживает:
    - Полный CRUD цикл (GET / POST / PUT / PATCH / DELETE)
    - Фильтрацию по категории, статусу и флагам
    - Фильтрацию с учётом дочерних категорий (?include_child_categories=true)
    - Поиск по name, description и IPN (?search=<term>)
    - Сортировку (?ordering=creation_date)
    - Пагинацию (?page=1&page_size=25)
    - Кастомные actions для управления ревизиями
    """
    serializer_class = PartSerializer
    pagination_class = StandardPagination

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # category убран из filterset_fields — обрабатывается вручную в get_queryset,
    # чтобы DjangoFilterBackend не конфликтовал с логикой include_child_categories.
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['active', 'virtual', 'template', 'assembly', 'component']
    search_fields = ['name', 'description', 'IPN']
    ordering_fields = ['id', 'name', 'IPN', 'creation_date']
    ordering = ['-creation_date']  # новые детали первыми

    def get_queryset(self):
        """
        Оптимизированный queryset:
        - select_related для FK (category, revision_of) — устранение N+1
        - аннотации stock_count и bom_count на уровне БД
        - поддержка параметра include_child_categories
        - ручная фильтрация по category (чтобы не конфликтовать с DjangoFilterBackend)
        """
        qs = Part.objects.select_related(
            'category', 'revision_of'
        ).annotate(
            stock_count=Sum('stock_items__quantity'),
            bom_count=Count('bom_items'),
        )

        category_id = self.request.query_params.get('category')
        include_children = self.request.query_params.get('include_child_categories', '').lower()

        if category_id:
            if include_children in ('true', '1', 'yes'):
                # Включаем все дочерние категории через BFS
                try:
                    root_category = PartCategory.objects.get(pk=category_id)
                    descendants = root_category.get_descendants(include_self=True)
                    descendant_ids = [cat.pk for cat in descendants]
                    qs = qs.filter(category_id__in=descendant_ids)
                except PartCategory.DoesNotExist:
                    qs = qs.none()
            else:
                # Стандартная фильтрация по точному совпадению категории
                try:
                    qs = qs.filter(category_id=int(category_id))
                except (ValueError, TypeError):
                    qs = qs.none()

        return qs

    # ------------------------------------------------------------------
    # GET /api/part/<pk>/revisions/
    # Список всех ревизий конкретной детали
    # ------------------------------------------------------------------
    @action(detail=True, methods=['get'], url_path='revisions')
    def list_revisions(self, request, pk=None):
        """
        Возвращает все ревизии, созданные на основе данной детали.
        Ревизия — это деталь, у которой revision_of указывает на текущую.
        """
        part = self.get_object()
        revisions = Part.objects.filter(revision_of=part).order_by('-creation_date')

        page = self.paginate_queryset(revisions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(revisions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # POST /api/part/<pk>/create_revision/
    # Создание новой ревизии на основе существующей детали
    # ------------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='create_revision',
            permission_classes=[permissions.IsAuthenticated])
    def create_revision(self, request, pk=None):
        """
        Создаёт новую ревизию текущей детали.

        Обязательные поля в теле запроса:
        - revision (str): код ревизии, например "B", "v2", "rev3"

        Опциональные поля:
        - name, description, IPN — если не указаны, копируются из оригинала.
        """
        original_part = self.get_object()

        # Код ревизии обязателен
        revision_code = request.data.get('revision')
        if not revision_code:
            return Response(
                {"revision": "Код ревизии обязателен для создания новой версии."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Валидация длины кода ревизии (max_length=20 в модели)
        if len(str(revision_code)) > 20:
            return Response(
                {
                    "error_code": "BAD_REQUEST",
                    "message": "Ошибка валидации данных.",
                    "details": {"revision": ["Код ревизии не может превышать 20 символов."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Нельзя создавать ревизию неактивной детали
        if not original_part.active:
            return Response(
                {
                    "error_code": "BAD_REQUEST",
                    "message": "Ошибка валидации данных.",
                    "details": {"detail": ["Нельзя создать ревизию для неактивной детали."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Проверка: нельзя дублировать код ревизии в рамках одного мастер-парта
        if Part.objects.filter(revision_of=original_part, revision=revision_code).exists():
            return Response(
                {"revision": f"Ревизия '{revision_code}' уже существует для данной детали."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Подготовка данных новой ревизии (наследование от оригинала)
        revision_data = {
            'name': request.data.get('name', original_part.name),
            'description': request.data.get('description', original_part.description),
            'IPN': request.data.get('IPN'),  # IPN должен быть уникальным — не копируем
            'category': original_part.category,
            'revision_of': original_part,
            'revision': revision_code,
            'active': request.data.get('active', original_part.active),
            'virtual': original_part.virtual,
            'template': original_part.template,
            'assembly': original_part.assembly,
            'component': original_part.component,
        }

        new_revision = Part.objects.create(**revision_data)
        serializer = self.get_serializer(new_revision)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # DELETE /api/part/<pk>/revisions/clear/
    # Удаление всех ревизий детали
    # ------------------------------------------------------------------
    @action(detail=True, methods=['delete'], url_path='revisions/clear',
            permission_classes=[permissions.IsAuthenticated])
    def clear_revisions(self, request, pk=None):
        """Удаляет все ревизии, привязанные к данной детали."""
        part = self.get_object()
        count, _ = Part.objects.filter(revision_of=part).delete()
        return Response(
            {"detail": f"Удалено ревизий: {count}."},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# BomItem ViewSet
# ---------------------------------------------------------------------------

class BomItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления Bill of Materials (BOM).

    Поддерживает:
    - CRUD операции для BOM-записей
    - Фильтрацию по assembly и sub_part
    - Поиск по именам деталей
    - Пагинацию
    """
    serializer_class = BomItemSerializer
    pagination_class = StandardPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['assembly', 'sub_part', 'optional']
    search_fields = ['assembly__name', 'sub_part__name']
    ordering_fields = ['id', 'quantity']
    ordering = ['id']

    def get_queryset(self):
        """Оптимизация: select_related для устранения N+1 при сериализации."""
        return BomItem.objects.select_related('assembly', 'sub_part')


# ---------------------------------------------------------------------------
# StockItem ViewSet
# ---------------------------------------------------------------------------

class StockItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления складскими остатками (StockItem).

    Поддерживает:
    - CRUD операции для складских записей
    - Фильтрацию по детали, местоположению и партии
    - Поиск по имени детали и местоположению
    - Пагинацию
    """
    serializer_class = StockItemSerializer
    pagination_class = StandardPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['part', 'location', 'batch']
    search_fields = ['part__name', 'location', 'batch']
    ordering_fields = ['id', 'quantity', 'created']
    ordering = ['-created']

    def get_queryset(self):
        """Оптимизация: select_related для устранения N+1."""
        return StockItem.objects.select_related('part')
