from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator


# Unidades de medida de materiales
class Unit(models.Model):
    name = models.CharField("Nombre", max_length=50, unique=True)
    symbol = models.CharField("Símbolo", max_length=10, unique=True)

    class Meta:
        unique_together = ("name", "symbol")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.symbol})"


# Materiales
class Material(models.Model):
    # 1) SKU: 3 letras + '-' + 1 a 4 dígitos. Ej: ABC-1, ABC-1234
    sku_validator = RegexValidator(
        regex=r"^[A-Z]{3}-\d{1,4}$",
        message="El código debe tener 3 letras, un guion y 1–4 dígitos (p. ej. ABC-1234).",
    )
    sku = models.CharField(
        "Código", max_length=8, unique=True, validators=[sku_validator]
    )

    name = models.CharField("Nombre", max_length=120)

    # 3) Categoría como lista desplegable
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
    category = models.CharField(
        "Categoría", max_length=20, choices=CATEGORIES, default="OTROS"
    )

    stock = models.DecimalField(
        "Stock global disponible",
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    def stock_en_proyecto(self, proyecto):
        """
        Devuelve el stock de este material asignado a un proyecto específico.
        """
        pm = self.proyectos.filter(pk=proyecto.pk).first()
        if pm:
            pm_rel = self.proyectomaterial_set.filter(proyecto=proyecto).first()
            return pm_rel.stock_proyecto if pm_rel else 0
        return 0

    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="materials")

    # 4) Cantidad de esa unidad para el material (presentación). Ej: bulto de 50 kg => 50
    presentation_qty = models.DecimalField(
        "Cantidad por unidad de medida",
        max_digits=12,
        decimal_places=3,
        default=1,
        validators=[MinValueValidator(0.001)],
        help_text="Ej.: si el bulto es de 50 kg, aquí va 50 (unidad = kg).",
    )

    # 5) COP sin decimales
    unit_cost = models.DecimalField(
        "Costo unitario (COP)",
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
    )

    # Imagen opcional del material
    image = models.ImageField(
        "Imagen", upload_to="materials/%Y/%m/", blank=True, null=True
    )

    created_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["sku"])]

    def __str__(self):
        return f"{self.sku} — {self.name}"


# Proveedor
class Supplier(models.Model):
    name = models.CharField("Proveedor", max_length=120, unique=True)
    contact_name = models.CharField("Contacto", max_length=120, blank=True)
    phone = models.CharField("Teléfono", max_length=30, blank=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class MaterialSupplier(models.Model):
    material = models.ForeignKey(
        "Material", on_delete=models.CASCADE, related_name="supplier_prices"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name="material_prices"
    )
    price = models.DecimalField(
        "Precio (COP)",
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )
    preferred = models.BooleanField("Proveedor principal", default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("material", "supplier")
        ordering = ["-preferred", "supplier__name"]

    def __str__(self):
        return f"{self.material.sku} · {self.supplier.name} · ${self.price:.0f} COP"
