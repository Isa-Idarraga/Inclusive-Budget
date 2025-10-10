from django.contrib import admin
from .models import Project, UnitPrice, BudgetSection, BudgetItem, ProjectBudgetItem


@admin.register(UnitPrice)
class UnitPriceAdmin(admin.ModelAdmin):
    list_display = ["item_name", "category", "price", "unit", "is_active", "updated_at"]
    list_filter = ["category", "is_active", "created_at"]
    search_fields = ["item_name", "description"]
    list_editable = ["price", "is_active"]
    ordering = ["category", "item_name"]

    fieldsets = (
        (
            "Información del Precio",
            {"fields": ("category", "item_name", "unit", "price", "is_active")},
        ),
        ("Descripción", {"fields": ("description",), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "ubicacion_proyecto",
        "estado",
        "area_construida_total",
        "numero_pisos",
        "creado_por",
        "fecha_creacion",
        "presupuesto",
    ]
    list_filter = [
        "estado",
        "ubicacion_proyecto",
        "numero_pisos",
        "fecha_creacion",
        "creado_por",
    ]
    search_fields = ["name", "location_address", "description"]
    readonly_fields = ["fecha_creacion", "fecha_actualizacion"]

    fieldsets = (
        (
            "Información Básica",
            {
                "fields": (
                    "name",
                    "location_address",
                    "description",
                    "estado",
                    "imagen_proyecto",
                )
            },
        ),
        (
            "1. Datos Generales del Proyecto",
            {
                "fields": (
                    "ubicacion_proyecto",
                    "otra_ubicacion",
                    "area_construida_total",
                    "numero_pisos",
                    "area_exterior_intervenir",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "2. Terreno y Preliminares",
            {
                "fields": ("tipo_terreno", "acceso_obra", "requiere_cerramiento"),
                "classes": ("collapse",),
            },
        ),
        (
            "3. Estructura y Cimentación",
            {
                "fields": ("sistema_entrepiso", "exigencia_estructural"),
                "classes": ("collapse",),
            },
        ),
        (
            "4. Muros y Acabados Básicos",
            {
                "fields": ("relacion_muros", "acabado_muros", "cielorrasos"),
                "classes": ("collapse",),
            },
        ),
        (
            "5. Pisos y Enchapes",
            {
                "fields": (
                    "piso_zona_social",
                    "piso_habitaciones",
                    "numero_banos",
                    "nivel_enchape_banos",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "6. Carpinterías",
            {
                "fields": (
                    "puertas_interiores",
                    "puerta_principal_especial",
                    "porcentaje_ventanas",
                    "metros_mueble_cocina",
                    "vestier_closets",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "7. Hidrosanitario",
            {
                "fields": (
                    "calentador_gas",
                    "incluye_lavadero",
                    "punto_lavaplatos",
                    "punto_lavadora",
                    "punto_lavadero",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "8. Instalaciones Eléctricas y Gas",
            {
                "fields": ("dotacion_electrica", "red_gas_natural"),
                "classes": ("collapse",),
            },
        ),
        (
            "9. Cubierta e Impermeabilización",
            {
                "fields": ("tipo_cubierta", "impermeabilizacion_adicional"),
                "classes": ("collapse",),
            },
        ),
        (
            "10. Exteriores y Paisajismo",
            {"fields": ("area_adoquin", "area_zonas_verdes"), "classes": ("collapse",)},
        ),
        (
            "11. Indirectos y Profesionales",
            {
                "fields": ("incluir_estudios_disenos", "incluir_licencia_impuestos"),
                "classes": ("collapse",),
            },
        ),
        (
            "Campos Heredados (Compatibilidad)",
            {
                "fields": (
                    "built_area",
                    "exterior_area",
                    "columns_count",
                    "walls_area",
                    "windows_area",
                    "doors_count",
                    "doors_height",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Presupuesto", {"fields": ("presupuesto", "presupuesto_gastado")}),
        (
            "Información del Sistema",
            {
                "fields": ("creado_por", "fecha_creacion", "fecha_actualizacion"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo proyecto
            obj.creado_por = request.user
        # Calcular campos heredados automáticamente
        obj.calculate_legacy_fields()
        # Calcular presupuesto automáticamente al guardar
        obj.presupuesto = obj.calculate_detailed_budget()
        super().save_model(request, obj, form, change)

    actions = ["recalculate_budgets"]

    def recalculate_budgets(self, request, queryset):
        """Acción para recalcular presupuestos de proyectos seleccionados"""
        updated = 0
        for project in queryset:
            # Calcular campos heredados
            project.calculate_legacy_fields()
            # Calcular presupuesto
            project.presupuesto = project.calculate_detailed_budget()
            project.save()
            updated += 1

        self.message_user(
            request,
            f"Se recalcularon {updated} presupuestos y campos heredados exitosamente.",
        )

    recalculate_budgets.short_description = "Recalcular presupuestos seleccionados"


@admin.register(BudgetSection)
class BudgetSectionAdmin(admin.ModelAdmin):
    list_display = ["order", "name", "is_percentage", "percentage_value"]
    list_editable = ["is_percentage", "percentage_value"]
    list_display_links = ["name"]
    ordering = ["order"]
    search_fields = ["name", "description"]


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ["section", "code", "description", "unit", "unit_price", "is_active"]
    list_filter = ["section", "is_active"]
    list_editable = ["unit_price", "is_active"]
    list_display_links = ["description"]
    search_fields = ["description", "code"]
    ordering = ["section__order", "order"]
    
    fieldsets = (
        ("Información Básica", {
            "fields": ("section", "code", "description", "unit")
        }),
        ("Precios", {
            "fields": ("unit_price", "is_active")
        }),
    )


@admin.register(ProjectBudgetItem)
class ProjectBudgetItemAdmin(admin.ModelAdmin):
    list_display = ["project", "budget_item", "quantity", "unit_price", "total_price"]
    list_filter = ["project", "budget_item__section"]
    search_fields = ["project__name", "budget_item__description"]
    readonly_fields = ["total_price"]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'budget_item', 'budget_item__section')
