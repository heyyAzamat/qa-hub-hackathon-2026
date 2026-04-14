from django.db import models


class PartCategory(models.Model):
    """
    Модель для классификации деталей.
    Поддерживает иерархическую структуру категорий.
    """
    name = models.CharField(max_length=100, verbose_name='Наименование категории')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    
    # Рекурсивная связь для поддержки подкатегорий
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        related_name='children',
        verbose_name='Родительская категория'
    )

    def __str__(self):
        return f"{self.name} (ID: {self.id})"

    def get_descendants(self, include_self=False):
        """
        Рекурсивно собирает все дочерние категории (для фильтрации
        деталей по ветке дерева без MPTT-библиотеки).
        Использует BFS для предотвращения глубокой рекурсии.
        """
        descendants = []
        if include_self:
            descendants.append(self)
        queue = list(self.children.all())
        visited = {self.pk}
        while queue:
            node = queue.pop(0)
            if node.pk in visited:
                continue
            visited.add(node.pk)
            descendants.append(node)
            queue.extend(list(node.children.all()))
        return descendants

    class Meta:
        verbose_name = 'Категория детали'
        verbose_name_plural = 'Категории деталей'


class Part(models.Model):
    """
    Центральная модель для хранения информации о деталях.
    """
    name = models.CharField(max_length=200, verbose_name='Наименование')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    
    # Internal Part Number — уникальный внутренний номер детали
    IPN = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='Внутренний номер')
    
    # Привязка детали к категории
    category = models.ForeignKey(
        PartCategory, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='parts',
        verbose_name='Категория'
    )

    # Логические флаги по ТЗ
    active = models.BooleanField(default=True, verbose_name='Активна')
    virtual = models.BooleanField(default=False, verbose_name='Виртуальная')
    template = models.BooleanField(default=False, verbose_name='Шаблон')
    assembly = models.BooleanField(default=False, verbose_name='Сборка')
    component = models.BooleanField(default=True, verbose_name='Компонент')

    # Поля для поддержки ревизий (версий) детали
    revision_of = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='revisions',
        verbose_name='Ревизия из детали'
    )
    revision = models.CharField(max_length=20, blank=True, null=True, verbose_name='Код ревизии')

    # Системные поля
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f"[{self.IPN}] {self.name}" if self.IPN else self.name

    class Meta:
        verbose_name = 'Деталь'
        verbose_name_plural = 'Детали'
        indexes = [
            # Составной индекс: быстрый поиск деталей по категории + статусу
            models.Index(fields=['category', 'active'], name='idx_part_category_active'),
            # Индекс на IPN для быстрых проверок уникальности
            models.Index(fields=['IPN'], name='idx_part_ipn'),
        ]


class BomItem(models.Model):
    """
    Bill of Materials — запись о том, что деталь-сборка (assembly)
    состоит из указанного компонента (sub_part) в заданном количестве.
    
    Используется для построения дерева спецификаций.
    """
    # Деталь-сборка, которой принадлежит этот BOM-элемент
    assembly = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='bom_items',
        verbose_name='Сборка (родитель)',
        help_text='Деталь, для которой указывается состав.',
    )
    # Компонент, входящий в состав сборки
    sub_part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='used_in',
        verbose_name='Компонент (подчинённая деталь)',
        help_text='Деталь, которая входит в состав сборки.',
    )
    # Количество единиц компонента, требуемых для одной сборки
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        default=1,
        verbose_name='Количество',
    )
    # Является ли компонент опциональным
    optional = models.BooleanField(default=False, verbose_name='Опциональный')
    # Пользовательские заметки
    note = models.TextField(blank=True, null=True, verbose_name='Примечание')

    def __str__(self):
        return f"{self.assembly.name} → {self.sub_part.name} x{self.quantity}"

    class Meta:
        verbose_name = 'Элемент спецификации (BOM)'
        verbose_name_plural = 'Элементы спецификации (BOM)'
        # Уникальная пара: одна сборка не может содержать один и тот же компонент дважды
        unique_together = [('assembly', 'sub_part')]
        indexes = [
            models.Index(fields=['assembly'], name='idx_bom_assembly'),
            models.Index(fields=['sub_part'], name='idx_bom_sub_part'),
        ]


class StockItem(models.Model):
    """
    Складской остаток для конкретной детали.
    Шаблонные детали (template=True) не могут иметь записей StockItem.
    """
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='stock_items',
        verbose_name='Деталь',
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        default=0,
        verbose_name='Количество на складе',
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Местоположение',
    )
    batch = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Номер партии',
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='Дата поступления')

    def __str__(self):
        return f"{self.part.name}: {self.quantity} шт."

    class Meta:
        verbose_name = 'Складской остаток'
        verbose_name_plural = 'Складские остатки'
