import typing
from rest_framework import serializers

from .models import Part, PartCategory, BomItem, StockItem


# ---------------------------------------------------------------------------
# PartCategory Serializer
# ---------------------------------------------------------------------------

class PartCategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для сущности PartCategory.
    Обеспечивает работу с иерархическим деревом категорий через parent/children.
    """

    # Read-only поле для вывода вложенных категорий
    children = serializers.SerializerMethodField(read_only=True)
    # Количество деталей в категории (аннотируется во ViewSet)
    part_count = serializers.IntegerField(read_only=True, required=False, default=0)

    class Meta:
        model = PartCategory
        fields = ['id', 'name', 'description', 'parent', 'children', 'part_count']
        read_only_fields = ['id']

    def get_children(self, obj: typing.Any) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Рекурсивно извлекает сериализованные дочерние категории.

        :param obj: Экземпляр текущей категории.
        :return: Список сериализованных дочерних категорий.
        """
        if hasattr(obj, 'children') and obj.children.exists():
            return PartCategorySerializer(
                obj.children.all(),
                many=True,
                context=self.context
            ).data
        return []

    def validate(self, attrs: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """
        Выполняет валидацию бизнес-логики категории.
        Проверяет наличие циклических зависимостей древовидной структуры.
        """
        parent = attrs.get('parent')

        if parent and self.instance:
            current_parent = parent
            visited_ids = set()
            while current_parent is not None:
                if current_parent.id == self.instance.id:
                    raise serializers.ValidationError(
                        {"parent": "Обнаружена циклическая зависимость: категория не может ссылаться на себя или своих потомков."}
                    )
                if current_parent.id in visited_ids:
                    break
                visited_ids.add(current_parent.id)
                current_parent = current_parent.parent

        return attrs


class PartCategoryTreeSerializer(serializers.ModelSerializer):
    """
    Легковесный сериализатор для отображения полного дерева категорий.
    Не тянет part_count — используется для быстрой навигации.
    """
    children = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PartCategory
        fields = ['id', 'name', 'parent', 'children']
        read_only_fields = ['id']

    def get_children(self, obj: typing.Any) -> typing.List[typing.Dict[str, typing.Any]]:
        children_qs = obj.children.all()
        if children_qs.exists():
            return PartCategoryTreeSerializer(children_qs, many=True, context=self.context).data
        return []


# ---------------------------------------------------------------------------
# Part Serializer
# ---------------------------------------------------------------------------

class PartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для сущности Part.
    Обрабатывает основные атрибуты детали, параметры, привязку к категории,
    и выполняет строгую бизнес-валидацию перед сохранением.
    """

    # Позволяет передать ID существующей категории при создании/обновлении (Write-only)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=PartCategory.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    # Полное отображение категории в теле ответа (Read-only)
    category = PartCategorySerializer(read_only=True)

    # Read-only извлечение привязанных параметров (Part Parameters)
    parameters = serializers.SerializerMethodField(read_only=True)

    # Read-only аннотации для числовых метрик
    stock_count = serializers.DecimalField(
        max_digits=15, decimal_places=5,
        read_only=True, required=False, default=0
    )
    bom_count = serializers.IntegerField(read_only=True, required=False, default=0)

    # Логические флаги
    active = serializers.BooleanField(default=True)
    virtual = serializers.BooleanField(default=False)
    template = serializers.BooleanField(default=False)
    assembly = serializers.BooleanField(default=False)
    component = serializers.BooleanField(default=True)

    class Meta:
        model = Part
        fields = [
            'id', 'name', 'description', 'IPN', 'revision_of', 'revision',
            'active', 'virtual', 'template', 'assembly', 'component',
            'category', 'category_id', 'creation_date', 'parameters',
            'stock_count', 'bom_count',
        ]
        # Системные поля защищаются от ручных изменений
        read_only_fields = ['id', 'creation_date']

    def get_parameters(self, obj: typing.Any) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Возвращает список привязанных параметров детали.

        :param obj: Экземпляр текущей детали.
        :return: Список словарей с именами и значениями параметров.
        """
        if hasattr(obj, 'parameters') and obj.parameters.exists():
            return [
                {
                    "name": getattr(param.template, 'name', None) if hasattr(param, 'template') else None,
                    "data": getattr(param, 'data', None)
                }
                for param in obj.parameters.all()
            ]
        return []

    def validate_IPN(self, value: str) -> str:
        """
        [Требование 2] Проверка уникальности Внутреннего Номера Детали (IPN).
        """
        if value:
            query = Part.objects.filter(IPN=value)
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError("Деталь с таким IPN уже существует в системе.")
        return value

    def validate_revision_of(self, value: typing.Any) -> typing.Any:
        """
        [Требование 1 и 3] Проверка логики ревизий.
        - Запрет циклической зависимости (Edge Case).
        - Запрет на привязку к неактивной детали.
        """
        if not value:
            return value

        # Ограничения Inactive деталей: нельзя основывать ревизию на неактивной
        if hasattr(value, 'active') and not value.active:
            raise serializers.ValidationError(
                "Невозможно создать ревизию от деактивированной (Inactive) детали."
            )

        # Предотвращение циклической зависимости
        if self.instance:
            current_link = value
            visited_ids = {self.instance.id}
            while current_link is not None:
                if current_link.id in visited_ids:
                    raise serializers.ValidationError(
                        "Обнаружена циклическая зависимость ревизий. Разрыв связи."
                    )
                visited_ids.add(current_link.id)
                current_link = getattr(current_link, 'revision_of', None)
                
        return value

    def validate_active(self, value: bool) -> bool:
        """
        [Требование 3] Дополнительные ограничения для деактивируемых деталей.
        - Деталь нельзя деактивировать, если у неё есть активные дочерние ревизии.
        """
        if self.instance and getattr(self.instance, 'active', True) and not value:
            active_children = Part.objects.filter(revision_of=self.instance, active=True).exists()
            if active_children:
                raise serializers.ValidationError(
                    "Нельзя деактивировать деталь, пока у неё есть активные дочерние ревизии."
                )
        return value

    def validate(self, attrs: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """
        Глобальная кросс-полевая валидация бизнес-логики.
        """
        # Строгая проверка того, что имя и описание не состоят из одних пробелов
        name = attrs.get('name', getattr(self.instance, 'name', ''))
        description = attrs.get('description', getattr(self.instance, 'description', ''))

        if not name or not str(name).strip():
            raise serializers.ValidationError({"name": "Поле 'Name' не может быть пустым."})
        if not description or not str(description).strip():
            raise serializers.ValidationError({"description": "Поле 'Description' не может быть пустым."})

        # -------------------------------------------------------------------
        # [Improvement Plan 2.4] Запрет снятия флага assembly, если у детали
        # есть привязанные BOM-компоненты
        # -------------------------------------------------------------------
        if self.instance:
            new_assembly = attrs.get('assembly', self.instance.assembly)
            if self.instance.assembly and not new_assembly:
                if BomItem.objects.filter(assembly=self.instance).exists():
                    raise serializers.ValidationError({
                        "assembly": "Нельзя снять флаг 'Сборка', пока у детали есть привязанные компоненты (BOM items). "
                                    "Сначала удалите все BOM-записи."
                    })

        return attrs


# ---------------------------------------------------------------------------
# BomItem Serializer
# ---------------------------------------------------------------------------

class BomItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Bill of Materials.
    Обеспечивает CRUD для компонентов сборки с защитой от:
    - циклических зависимостей (A→B→A)
    - добавления неактивных компонентов
    - привязки компонента к не-сборке
    - добавления сборке самой себя
    """

    # Read-only: отображение имён деталей для удобства
    assembly_name = serializers.CharField(source='assembly.name', read_only=True)
    sub_part_name = serializers.CharField(source='sub_part.name', read_only=True)

    class Meta:
        model = BomItem
        fields = [
            'id', 'assembly', 'sub_part', 'quantity', 'optional', 'note',
            'assembly_name', 'sub_part_name',
        ]
        read_only_fields = ['id']

    def validate_quantity(self, value):
        """Количество компонента должно быть положительным."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Количество должно быть больше нуля.")
        return value

    def validate(self, attrs: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """
        Кросс-полевая валидация BOM-записи.
        """
        assembly_part = attrs.get('assembly', getattr(self.instance, 'assembly', None))
        sub_part = attrs.get('sub_part', getattr(self.instance, 'sub_part', None))

        if assembly_part and sub_part:
            # 1. Деталь не может быть компонентом самой себя
            if assembly_part.pk == sub_part.pk:
                raise serializers.ValidationError(
                    {"sub_part": "Деталь не может являться компонентом самой себя."}
                )

            # 2. Родитель должен быть сборкой (assembly=True)
            if not assembly_part.assembly:
                raise serializers.ValidationError(
                    {"assembly": f"Деталь '{assembly_part.name}' не является сборкой (assembly=False). "
                                 "Установите флаг 'assembly' перед добавлением компонентов."}
                )

            # 3. Компонент должен быть помечен как component=True
            if not sub_part.component:
                raise serializers.ValidationError(
                    {"sub_part": f"Деталь '{sub_part.name}' не является компонентом (component=False)."}
                )

            # 4. Запрет на добавление неактивного компонента
            if not sub_part.active:
                raise serializers.ValidationError(
                    {"sub_part": f"Деталь '{sub_part.name}' деактивирована и не может быть добавлена в спецификацию."}
                )

            # 5. Защита от циклических зависимостей (BFS по дереву BOM)
            if self._creates_cycle(assembly_part, sub_part):
                raise serializers.ValidationError(
                    {"sub_part": "Обнаружена циклическая зависимость в BOM: "
                                 f"'{sub_part.name}' уже содержит '{assembly_part.name}' "
                                 "в своём дереве спецификаций (прямо или транзитивно)."}
                )

        return attrs

    @staticmethod
    def _creates_cycle(assembly_part, new_sub_part) -> bool:
        """
        Проверяет, приведёт ли добавление new_sub_part в BOM assembly_part
        к циклической зависимости.

        Алгоритм BFS: начинаем от new_sub_part и обходим все его собственные
        BOM-компоненты вглубь. Если встретим assembly_part — цикл обнаружен.
        """
        visited = set()
        queue = [new_sub_part.pk]

        while queue:
            current_pk = queue.pop(0)
            if current_pk == assembly_part.pk:
                return True
            if current_pk in visited:
                continue
            visited.add(current_pk)

            # Получаем все компоненты, в которые входит текущая деталь как сборка
            child_pks = list(
                BomItem.objects.filter(assembly_id=current_pk).values_list('sub_part_id', flat=True)
            )
            queue.extend(child_pks)

        return False


# ---------------------------------------------------------------------------
# StockItem Serializer
# ---------------------------------------------------------------------------

class StockItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для складских остатков.
    Блокирует создание Stock для шаблонных деталей (template=True).
    """

    part_name = serializers.CharField(source='part.name', read_only=True)

    class Meta:
        model = StockItem
        fields = ['id', 'part', 'part_name', 'quantity', 'location', 'batch', 'created']
        read_only_fields = ['id', 'created']

    def validate_quantity(self, value):
        """Количество на складе не может быть отрицательным."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Количество на складе не может быть отрицательным.")
        return value

    def validate_part(self, value):
        """
        [Improvement Plan 2.3] Блокировка создания складских остатков
        для шаблонных деталей.
        """
        if value and value.template:
            raise serializers.ValidationError(
                f"Деталь '{value.name}' является шаблоном (template=True). "
                "Шаблонные детали не могут иметь складских остатков — "
                "используйте конкретные вариации шаблона."
            )
        return value
