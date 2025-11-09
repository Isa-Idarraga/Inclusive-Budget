# Generated manually for safe category migration
import django.db.models.deletion
from django.db import migrations, models


def populate_categories(apps, schema_editor):
    """
    Puebla la tabla Category con las categorías existentes
    y migra los materiales existentes a las nuevas categorías
    """
    Category = apps.get_model('catalog', 'Category')
    Material = apps.get_model('catalog', 'Material')
    
    # Categorías originales del modelo
    CATEGORIES = [
        ("CEMENTOS", "Cementos"),
        ("AGREGADOS", "Agregados"),
        ("ACERO", "Acero"),
        ("MADERA", "Madera"),
        ("PINTURAS", "Pinturas"),
        ("ELECTRICOS", "Eléctricos"),
        ("HIDRAULICOS", "Hidráulicos"),
        ("LADRILLOS", "Ladrillos"),
        ("OTROS", "Otros"),
    ]
    
    # Crear las categorías
    category_map = {}
    for code, name in CATEGORIES:
        cat, created = Category.objects.get_or_create(
            code=code,
            defaults={'name': name}
        )
        category_map[code] = cat
        if created:
            print(f"✓ Categoría creada: {name} ({code})")
    
    # Migrar materiales existentes
    # Agregar temporalmente el campo old_category para guardar el valor actual
    pass  # Los materiales se migrarán en el paso siguiente


def reverse_categories(apps, schema_editor):
    """
    Revierte la creación de categorías (solo en caso de rollback)
    """
    Category = apps.get_model('catalog', 'Category')
    Category.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0008_merge_0007_material_stock_0007_stock_default_not_null"),
    ]

    operations = [
        # Paso 1: Crear el modelo Category
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=50, unique=True, verbose_name="Nombre"),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="Código interno en mayúsculas",
                        max_length=20,
                        unique=True,
                        verbose_name="Código",
                    ),
                ),
            ],
            options={
                "verbose_name": "Categoría",
                "verbose_name_plural": "Categorías",
                "ordering": ["name"],
            },
        ),
        
        # Paso 2: Poblar la tabla Category
        migrations.RunPython(populate_categories, reverse_categories),
        
        # Paso 3: Renombrar el campo actual a old_category
        migrations.RenameField(
            model_name='material',
            old_name='category',
            new_name='old_category',
        ),
        
        # Paso 4: Crear el nuevo campo category_id como ForeignKey (nullable temporalmente)
        migrations.AddField(
            model_name='material',
            name='category',
            field=models.ForeignKey(
                null=True,  # Temporal
                blank=True,  # Temporal
                on_delete=django.db.models.deletion.PROTECT,
                related_name="materials",
                to="catalog.category",
                verbose_name="Categoría",
            ),
        ),
        
        # Paso 5: Migrar los datos del campo viejo al nuevo
        migrations.RunPython(
            lambda apps, schema_editor: migrate_material_categories(apps, schema_editor),
            lambda apps, schema_editor: None
        ),
        
        # Paso 6: Hacer el campo NOT NULL
        migrations.AlterField(
            model_name='material',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="materials",
                to="catalog.category",
                verbose_name="Categoría",
            ),
        ),
        
        # Paso 7: Eliminar el campo viejo
        migrations.RemoveField(
            model_name='material',
            name='old_category',
        ),
        
        # Paso 8: Actualizar opciones de Unit
        migrations.AlterModelOptions(
            name="unit",
            options={
                "ordering": ["name"],
                "verbose_name": "Unidad de medida",
                "verbose_name_plural": "Unidades de medida",
            },
        ),
    ]


def migrate_material_categories(apps, schema_editor):
    """
    Migra los valores de old_category a category (ForeignKey)
    """
    Material = apps.get_model('catalog', 'Material')
    Category = apps.get_model('catalog', 'Category')
    
    # Mapear códigos a categorías
    categories = {cat.code: cat for cat in Category.objects.all()}
    
    # Migrar cada material
    for material in Material.objects.all():
        old_cat_code = material.old_category
        if old_cat_code in categories:
            material.category = categories[old_cat_code]
            material.save(update_fields=['category'])
            print(f"✓ Material '{material.name}' migrado a categoría {old_cat_code}")
        else:
            # Si no existe, asignar a OTROS
            material.category = categories.get('OTROS')
            material.save(update_fields=['category'])
            print(f"⚠ Material '{material.name}' asignado a OTROS (categoría original: {old_cat_code})")
