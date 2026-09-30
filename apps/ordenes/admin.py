from django.contrib import admin
from .models import Orden, OrdenItem


class OrdenItemInline(admin.TabularInline):
    model = OrdenItem
    extra = 0
    readonly_fields = ('precio_unitario',)


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ('id', 'numero_orden', 'usuario', 'estado', 'total', 'stock_reincorporado', 'creado_en')
    list_filter = ('estado', 'stock_reincorporado', 'creado_en')
    search_fields = ('numero_orden', 'usuario__username')
    inlines = [OrdenItemInline]
