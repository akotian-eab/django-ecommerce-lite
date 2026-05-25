from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from shop.managers import OrderQuerySet, ProductQuerySet


class Category(models.Model):
    """
    Groups products for browsing and filtering.

    Supports nested categories via ``parent`` (e.g. Electronics → Laptops).
    Slugs are used in URLs; auto-generated from ``name`` when omitted.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")  # noqa: E501
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    A sellable item in the catalog.

    Each product belongs to one ``Category`` and is identified by a unique ``sku``.
    Use ``DecimalField`` for ``price`` to avoid floating-point rounding errors.
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Inventory(models.Model):
    """
    Stock levels for a single product.

    OneToOne with ``Product`` keeps catalog data separate from warehouse data.
    Access via ``product.inventory``; deleting a product removes its inventory row.
    """

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventory")
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "inventory"

    def __str__(self):
        return f"{self.product.name} ({self.quantity} in stock)"

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold


class Order(models.Model):
    """
    A customer's purchase, made up of one or more line items (``OrderItem``).

    Linked to Django's built-in ``User`` model. ``status`` tracks fulfillment
    progress; line totals are computed from related items, not stored here.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.get_status_display()})"

    @property
    def total(self):
        """
        Order total from line items.

        If the queryset was built with ``Order.objects.with_total()``, reads
        the SQL-computed ``total_amount`` annotation (no extra queries).
        Otherwise falls back to summing items in Python (fine for a single order).
        """
        if hasattr(self, "total_amount"):
            return self.total_amount or Decimal("0")
        return sum((item.line_total for item in self.items.all()), Decimal("0"))


class OrderItem(models.Model):
    """
    One line on an order: a product, quantity, and the price at purchase time.

    ``unit_price`` snapshots ``Product.price`` so historical orders stay correct
    even if catalog prices change later.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "product"], name="unique_product_per_order"),
        ]

    def __str__(self):
        return f"{self.quantity}× {self.product.name}"

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        if self.unit_price is None:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
