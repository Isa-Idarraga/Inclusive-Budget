from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Prefetch
from .models import Material, Supplier, MaterialSupplier
from .forms import MaterialForm
from django.db import transaction
from django.db.models import Q, Prefetch
from django.contrib import messages
from .forms import MaterialSupplierForm

@login_required
def material_list(request):
    q = (request.GET.get("q") or "").strip()
    prefetch = Prefetch(
        "supplier_prices",
        queryset=MaterialSupplier.objects.select_related("supplier").order_by("-preferred", "supplier__name")
    )
    materials = (
        Material.objects
        .select_related("unit")
        .prefetch_related(prefetch)
        .order_by("name")
    )
    if q:
        materials = materials.filter(Q(name__icontains=q) | Q(sku__icontains=q))

    return render(request, "catalog/material_list.html", {"materials": materials, "q": q})

@login_required
def material_create(request):
    if request.method == "POST":
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            if request.user.is_authenticated:
                obj.created_by = request.user
            obj.save()

            # proveedor por nombre
            supplier_name = form.cleaned_data["supplier_name"]
            supplier = Supplier.objects.filter(name__iexact=supplier_name).first()
            if not supplier:
                supplier = Supplier.objects.create(name=supplier_name, is_active=True)

            price = form.cleaned_data["supplier_price"]

            link, created = MaterialSupplier.objects.get_or_create(
                material=obj, supplier=supplier,
                defaults={"price": price, "preferred": True}
            )
            if not created:
                link.price = price
                link.preferred = True
                link.save(update_fields=["price", "preferred"])
            obj.supplier_prices.exclude(pk=link.pk).update(preferred=False)

            if hasattr(obj, "unit_cost"):
                obj.unit_cost = price
                obj.save(update_fields=["unit_cost"])

            messages.success(request, "Material creado correctamente.")
            return redirect("material_list")
    else:
        form = MaterialForm()
    return render(request, "catalog/material_form.html", {"form": form, "mode": "create"})

@login_required
def material_update(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == "POST":
        form = MaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            obj = form.save()

            supplier_name = form.cleaned_data["supplier_name"]
            supplier = Supplier.objects.filter(name__iexact=supplier_name).first()
            if not supplier:
                supplier = Supplier.objects.create(name=supplier_name, is_active=True)

            price = form.cleaned_data["supplier_price"]

            link, created = MaterialSupplier.objects.get_or_create(
                material=obj, supplier=supplier,
                defaults={"price": price, "preferred": True}
            )
            if not created:
                link.price = price
                link.preferred = True
                link.save(update_fields=["price", "preferred"])
            obj.supplier_prices.exclude(pk=link.pk).update(preferred=False)

            if hasattr(obj, "unit_cost"):
                obj.unit_cost = price
                obj.save(update_fields=["unit_cost"])

            messages.success(request, "Material actualizado.")
            return redirect("material_list")
    else:
        form = MaterialForm(instance=material)
    return render(request, "catalog/material_form.html", {"form": form, "mode": "update", "material": material})

@login_required
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == "POST":
        # borra el archivo de imagen del disco si existe
        if material.image:
            material.image.delete(save=False)
        material.delete()
        messages.success(request, "Material eliminado.")
        return redirect("material_list")
    return render(request, "catalog/material_delete_confirm.html", {"material": material})

@login_required
def material_suppliers_list(request, material_id):
    material = get_object_or_404(
        Material.objects.select_related("unit"),
        pk=material_id
    )
    links = (
        material.supplier_prices
        .select_related("supplier")
        .order_by("-preferred", "supplier__name")
    )
    return render(request, "catalog/material_suppliers_list.html", {
        "material": material,
        "links": links,
    })


@login_required
@transaction.atomic
def material_supplier_create(request, material_id):
    material = get_object_or_404(Material, pk=material_id)
    if request.method == "POST":
        form = MaterialSupplierForm(request.POST, material=material)  # ⬅️ aquí
        if form.is_valid():
            name = form.cleaned_data["supplier_name"]
            supplier = Supplier.objects.filter(name__iexact=name).first() or Supplier.objects.create(name=name, is_active=True)
            price = form.cleaned_data["price"]
            preferred = form.cleaned_data["preferred"]

            link, created = MaterialSupplier.objects.get_or_create(
                material=material, supplier=supplier,
                defaults={'price': price, 'preferred': preferred}
            )
            if not created:
                link.price = price
                link.preferred = preferred or link.preferred
                link.save()

            if preferred:
                material.supplier_prices.exclude(pk=link.pk).update(preferred=False)
                if hasattr(material, "unit_cost"):
                    material.unit_cost = price
                    material.save(update_fields=["unit_cost"])

            messages.success(request, "Proveedor agregado al material.")
            return redirect("material_suppliers_list", material_id=material.pk)
    else:
        form = MaterialSupplierForm(material=material)  # ⬅️ aquí

    return render(request, "catalog/material_supplier_form.html", {
        "material": material,
        "form": form,
        "mode": "create",
    })

@login_required
@transaction.atomic
def material_supplier_update(request, material_id, link_id):
    material = get_object_or_404(Material, pk=material_id)
    link = get_object_or_404(MaterialSupplier.objects.select_related("supplier"), pk=link_id, material=material)

    if request.method == "POST":
        form = MaterialSupplierForm(request.POST, instance=link, material=material)  # ⬅️ aquí
        if form.is_valid():
            name = form.cleaned_data["supplier_name"]
            supplier = Supplier.objects.filter(name__iexact=name).first() or Supplier.objects.create(name=name, is_active=True)

            link.supplier = supplier
            link.price = form.cleaned_data["price"]
            link.preferred = form.cleaned_data["preferred"]
            link.save()

            if link.preferred:
                material.supplier_prices.exclude(pk=link.pk).update(preferred=False)
                if hasattr(material, "unit_cost"):
                    material.unit_cost = link.price
                    material.save(update_fields=["unit_cost"])

            messages.success(request, "Proveedor actualizado.")
            return redirect("material_suppliers_list", material_id=material.pk)
    else:
        form = MaterialSupplierForm(instance=link, material=material)  # ⬅️ aquí

    return render(request, "catalog/material_supplier_form.html", {
        "material": material,
        "form": form,
        "mode": "update",
        "link": link,
    })

@login_required
@transaction.atomic
def material_supplier_set_preferred(request, material_id, link_id):
    material = get_object_or_404(Material, pk=material_id)
    link = get_object_or_404(MaterialSupplier, pk=link_id, material=material)

    if request.method == "POST":
        material.supplier_prices.update(preferred=False)
        link.preferred = True
        link.save(update_fields=["preferred"])
        if hasattr(material, "unit_cost"):
            material.unit_cost = link.price
            material.save(update_fields=["unit_cost"])
        messages.success(request, "Proveedor marcado como preferido.")
    return redirect("material_suppliers_list", material_id=material.pk)


@login_required
@transaction.atomic
def material_supplier_delete(request, material_id, link_id):
    material = get_object_or_404(Material, pk=material_id)
    link = get_object_or_404(MaterialSupplier, pk=link_id, material=material)

    if request.method == "POST":
        link.delete()
        messages.success(request, "Proveedor eliminado del material.")
        return redirect("material_suppliers_list", material_id=material.pk)

    return render(request, "catalog/material_supplier_delete_confirm.html", {
        "material": material,
        "link": link,
    })
