from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin.sites import NotRegistered

from .models import Unit, Material, Category

# Asegura estado limpio por si hubo un registro previo
for model in (Unit, Material, Category):
    try:
        admin.site.unregister(model)
    except NotRegistered:
        pass


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "symbol")
    search_fields = ("name", "symbol")
    ordering = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
    ordering = ("name",)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    # columnas de la lista
    list_display = (
        "sku",
        "name",
        "category",
        "unit",
        "presentation_qty",
        "unit_cost_display",
        "thumb",
        "created_at",
    )
    list_filter = ("category", "unit")
    search_fields = ("sku", "name", "category__name")
    ordering = ("name",)
    list_per_page = 25
    autocomplete_fields = ("unit", "category")

    readonly_fields = ("image_preview", "created_at", "updated_at")
    fields = (
        "sku",
        "name",
        "category",
        "unit",
        "presentation_qty",
        "unit_cost",
        "image",
        "image_preview",
        "created_by",
        "created_at",
        "updated_at",
    )

    # helpers para mostrar bonito
    def unit_cost_display(self, obj):
        formatted = f"{obj.unit_cost:,.0f}".replace(",", ".")
        return format_html("${} COP", formatted)

    unit_cost_display.short_description = "Costo (COP)"
    unit_cost_display.admin_order_field = "unit_cost"

    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;" />',
                obj.image.url,
            )
        return "-"

    thumb.short_description = "Imagen"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:240px;max-height:240px;object-fit:cover;border-radius:6px;" />',
                obj.image.url,
            )
        return "Sin imagen"

    image_preview.short_description = "Vista previa"
