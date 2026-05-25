from django.contrib import admin

from shop.models import Category, Inventory, Order, OrderItem, Product


class InventoryInline(admin.StackedInline):
    model = Inventory
    max_num = 1
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active", "updated_at")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "is_active", "updated_at")
    list_filter = ("is_active", "category")
    search_fields = ("name", "slug", "sku")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    inlines = (InventoryInline,)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "low_stock_threshold", "is_low_stock", "updated_at")
    list_filter = ("quantity",)
    search_fields = ("product__name", "product__sku")
    autocomplete_fields = ("product",)

    @admin.display(boolean=True, description="Low stock")
    def is_low_stock(self, obj):
        return obj.is_low_stock


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ("product",)
    readonly_fields = ("line_total",)

    @admin.display(description="Line total")
    def line_total(self, obj):
        if obj.pk:
            return obj.line_total
        return "—"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "user__email")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at", "total")
    inlines = (OrderItemInline,)

    def get_queryset(self, request):
        """Use optimized queryset so list view totals don't N+1."""
        return super().get_queryset(request).with_total()

    @admin.display(description="Total")
    def total(self, obj):
        return obj.total


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "unit_price", "line_total")
    search_fields = ("product__name", "product__sku", "order__id")
    autocomplete_fields = ("order", "product")

    @admin.display(description="Line total")
    def line_total(self, obj):
        return obj.line_total
