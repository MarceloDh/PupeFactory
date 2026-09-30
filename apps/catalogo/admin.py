from django.contrib import admin
from .models import Categoria, Marca, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ('nombre',)


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'sku', 'categoria', 'marca', 'precio', 'stock', 'activo')
    list_filter = ('categoria', 'marca', 'activo')
    search_fields = ('nombre', 'sku')
    list_editable = ('precio', 'stock', 'activo')
