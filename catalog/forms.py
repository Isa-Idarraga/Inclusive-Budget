from django import forms
from .models import Material, Supplier, MaterialSupplier


# Widget numérico que desactiva localización y recorta ceros (.000 -> "")
class TrimmedNumberInput(forms.NumberInput):
    def format_value(self, value):
        s = super().format_value(value)
        if s in (None, ""):
            return s
        s = str(s).replace(",", ".")
        if s.count(".") > 1:
            first = s.find(".")
            s = s[: first + 1] + s[first + 1 :].replace(".", "")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s


class MaterialForm(forms.ModelForm):
    # Proveedor
    supplier_name = forms.CharField(
        label="Proveedor",
        max_length=120,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nombre del proveedor",
                "autocomplete": "off",
            }
        ),
    )
    supplier_price = forms.IntegerField(
        label="Precio con proveedor (COP)",
        min_value=0,
        required=True,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "1", "min": "0", "inputmode": "numeric"}
        ),
    )

    class Meta:
        model = Material
        fields = [
            "sku",
            "name",
            "category",
            "unit",
            "presentation_qty",
            "image",  # unit_cost
        ]
        widgets = {
            "sku": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "ABC-1234",
                    "maxlength": "8",
                    "autocomplete": "off",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre del material",
                    "autocomplete": "off",
                }
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "presentation_qty": TrimmedNumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.001",
                    "min": "0",
                    "inputmode": "decimal",
                }
            ),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        material = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        # Desactivar localización en numéricos
        for fname in ("presentation_qty",):
            f = self.fields.get(fname)
            if f:
                f.localize = False
                if getattr(f, "widget", None):
                    f.widget.is_localized = False
        # Si estamos editando, precarga proveedor/precio preferido
        if material:
            link = material.supplier_prices.order_by(
                "-preferred", "supplier__name"
            ).first()
            if link:
                self.fields["supplier_name"].initial = link.supplier.name
                self.fields["supplier_price"].initial = int(link.price)

    def clean_supplier_price(self):
        price = self.cleaned_data.get("supplier_price")
        if price is None:
            raise forms.ValidationError("Este campo es obligatorio.")
        if price <= 0:
            raise forms.ValidationError("El precio debe ser mayor a cero.")
        return price
    
    def clean_supplier_name(self):
        name = (self.cleaned_data.get("supplier_name") or "").strip()
        if not name:
            raise forms.ValidationError("Este campo es obligatorio.")
        # Normaliza espacios múltiples
        name = " ".join(name.split())
        return name

    # Normaliza SKU (3 letras - 1–4 dígitos)
    def clean_sku(self):
        raw = (self.cleaned_data.get("sku") or "").strip().upper()
        import re

        letters = re.sub(r"[^A-Z]", "", raw)[:3]
        digits = re.sub(r"\D", "", raw)[:4]
        return f"{letters}-{digits}" if letters and digits else raw


class MaterialSupplierForm(forms.ModelForm):
    supplier_name = forms.CharField(
        label="Proveedor",
        max_length=120,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nombre del proveedor",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = MaterialSupplier
        fields = ["supplier_name", "price", "preferred"]
        widgets = {
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "1",
                    "inputmode": "numeric",
                }
            ),
            "preferred": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "price": "Precio (COP)",
            "preferred": "Marcar como preferido",
        }

    def __init__(self, *args, **kwargs):
        self.material = kwargs.pop("material", None)
        instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        if instance and not self.material:
            self.material = instance.material
        if instance:
            self.fields["supplier_name"].initial = instance.supplier.name

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is None:
            raise forms.ValidationError("Este campo es obligatorio.")
        if price <= 0:
            raise forms.ValidationError("El precio debe ser mayor a cero.")
        return price
    
    def clean_supplier_name(self):
        name = (self.cleaned_data.get("supplier_name") or "").strip()
        if not name:
            raise forms.ValidationError("Este campo es obligatorio.")
        return " ".join(name.split())

    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("supplier_name")
        if not name or not self.material:
            return cleaned
        supplier = Supplier.objects.filter(name__iexact=name).first()
        if supplier:
            qs = MaterialSupplier.objects.filter(
                material=self.material, supplier=supplier
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "Este material ya tiene registrado a ese proveedor."
                )
        return cleaned
