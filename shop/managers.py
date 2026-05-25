"""
Custom managers and querysets for the shop app.

Pattern: define a ``QuerySet`` subclass with chainable methods, then expose
those methods on the manager via ``QuerySet.as_manager()``. This is more
flexible than subclassing ``Manager`` directly because chaining still works:

    Product.objects.active().in_stock().in_category("Audio")
"""

from __future__ import annotations

from django.db import models
from django.db.models import DecimalField, F, Sum


class ProductQuerySet(models.QuerySet):
    """Chainable queries for ``Product``."""

    def active(self) -> "ProductQuerySet":
        """Only products flagged as active in the catalog."""
        return self.filter(is_active=True)

    def in_stock(self) -> "ProductQuerySet":
        """Only products whose inventory has at least one unit."""
        return self.filter(inventory__quantity__gt=0)

    def low_stock(self) -> "ProductQuerySet":
        """Only products at or below their inventory threshold."""
        return self.filter(inventory__quantity__lte=F("inventory__low_stock_threshold"))

    def in_category(self, name: str) -> "ProductQuerySet":
        """Products in the named category (case-insensitive)."""
        return self.filter(category__name__iexact=name)

    def priced_between(self, low, high) -> "ProductQuerySet":
        """Products with price in the inclusive range ``[low, high]``."""
        return self.filter(price__gte=low, price__lte=high)


class OrderQuerySet(models.QuerySet):
    """Chainable queries for ``Order``."""

    def with_total(self) -> "OrderQuerySet":
        """
        Annotate each order with ``total_amount`` computed in SQL.

        Use this for list views instead of calling the ``total`` property,
        which would otherwise issue one query per order (N+1).
        """
        return self.annotate(
            total_amount=Sum(
                F("items__quantity") * F("items__unit_price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )

    def with_items_and_products(self) -> "OrderQuerySet":
        """Prefetch line items and their products for detail views."""
        return self.prefetch_related("items__product")


ProductManager = ProductQuerySet.as_manager
