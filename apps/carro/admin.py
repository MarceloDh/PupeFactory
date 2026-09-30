from django.contrib import admin
from .models import Carrito, CarritoItem


class CarritoItemInline(admin.TabularInline):
    model = CarritoItem
    extra = 0


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'creado_en', 'actualizado_en', 'total_items', 'total')
    inlines = [CarritoItemInline]
