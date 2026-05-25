"""
Seed the database with sample data for Phase 2 (ORM deep dive).

Usage:
    python manage.py seed_data            # create sample data, skip if already present
    python manage.py seed_data --flush    # wipe shop tables and reseed from scratch

The command is idempotent: running it twice without --flush will not create
duplicates. It uses ``update_or_create`` / ``get_or_create`` keyed on natural
identifiers (slug, sku, username).
"""

from __future__ import annotations

import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from shop.models import Category, Inventory, Order, OrderItem, Product

User = get_user_model()


CATEGORIES = [
    {
        "name": "Electronics",
        "children": ["Laptops", "Audio"],
    },
    {
        "name": "Home & Kitchen",
        "children": ["Cookware"],
    },
    {
        "name": "Books",
        "children": ["Fiction", "Programming"],
    },
]

PRODUCTS = [
    ("Laptop Pro 14", "LAPTOP-PRO-14", "Laptops", Decimal("1499.00"), 12),
    ("Laptop Air 13", "LAPTOP-AIR-13", "Laptops", Decimal("999.00"), 25),
    ("Wireless Headphones", "AUDIO-WH-01", "Audio", Decimal("199.99"), 40),
    ("USB-C Speaker", "AUDIO-SPK-USB", "Audio", Decimal("79.50"), 3),
    ("Cast Iron Skillet", "KITCHEN-CIS-10", "Cookware", Decimal("45.00"), 18),
    ("Chef's Knife 8\"", "KITCHEN-KNF-8", "Cookware", Decimal("89.99"), 7),
    ("The Pragmatic Programmer", "BOOK-PRAG-PROG", "Programming", Decimal("39.99"), 50),
    ("Two Scoops of Django", "BOOK-2SCOOPS", "Programming", Decimal("47.00"), 4),
    ("Dune", "BOOK-DUNE", "Fiction", Decimal("18.00"), 30),
    ("Project Hail Mary", "BOOK-PHM", "Fiction", Decimal("16.50"), 2),
]

USERS = [
    {"username": "admin", "email": "admin@example.com", "is_superuser": True},
    {"username": "alice", "email": "alice@example.com", "is_superuser": False},
    {"username": "bob", "email": "bob@example.com", "is_superuser": False},
]

DEFAULT_PASSWORD = "password123"


class Command(BaseCommand):
    help = "Seed the database with sample categories, products, inventory, users, and orders."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all shop data (and seeded users) before reseeding.",
        )
        parser.add_argument(
            "--orders",
            type=int,
            default=5,
            help="Number of sample orders to create (default: 5).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for reproducible order generation (default: 42).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])

        if options["flush"]:
            self._flush()

        categories = self._seed_categories()
        products = self._seed_products(categories)
        self._seed_inventory(products)
        users = self._seed_users()
        self._seed_orders(users, products, count=options["orders"])

        self._summary()

    def _flush(self):
        self.stdout.write(self.style.WARNING("Flushing shop data and seeded users..."))
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Inventory.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(username__in=[u["username"] for u in USERS]).delete()

    def _seed_categories(self) -> dict[str, Category]:
        self.stdout.write("Seeding categories...")
        created: dict[str, Category] = {}
        for top in CATEGORIES:
            parent, _ = Category.objects.get_or_create(name=top["name"])
            created[top["name"]] = parent
            for child_name in top["children"]:
                child, _ = Category.objects.get_or_create(name=child_name, parent=parent)
                created[child_name] = child
        return created

    def _seed_products(self, categories: dict[str, Category]) -> list[Product]:
        self.stdout.write("Seeding products...")
        products: list[Product] = []
        for name, sku, category_name, price, _stock in PRODUCTS:
            product, _ = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": categories[category_name],
                    "price": price,
                    "description": f"Sample description for {name}.",
                    "is_active": True,
                },
            )
            products.append(product)
        return products

    def _seed_inventory(self, products: list[Product]) -> None:
        self.stdout.write("Seeding inventory...")
        stock_lookup = {sku: qty for _, sku, _, _, qty in PRODUCTS}
        for product in products:
            Inventory.objects.update_or_create(
                product=product,
                defaults={"quantity": stock_lookup[product.sku]},
            )

    def _seed_users(self) -> list[User]:
        self.stdout.write("Seeding users...")
        users: list[User] = []
        for spec in USERS:
            user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "is_staff": spec["is_superuser"],
                    "is_superuser": spec["is_superuser"],
                },
            )
            if created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()
            users.append(user)
        return users

    def _seed_orders(self, users: list[User], products: list[Product], count: int) -> None:
        existing = Order.objects.count()
        if existing:
            self.stdout.write(
                self.style.NOTICE(
                    f"Skipping orders: {existing} already exist (use --flush to regenerate)."
                )
            )
            return

        self.stdout.write(f"Seeding {count} orders...")
        customers = [u for u in users if not u.is_superuser]
        statuses = list(Order.Status)

        for i in range(count):
            user = random.choice(customers)
            order = Order.objects.create(
                user=user,
                status=random.choice(statuses),
            )
            picked = random.sample(products, k=random.randint(1, 3))
            for product in picked:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=random.randint(1, 4),
                )

    def _summary(self) -> None:
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write(f"  Categories: {Category.objects.count()}")
        self.stdout.write(f"  Products:   {Product.objects.count()}")
        self.stdout.write(f"  Inventory:  {Inventory.objects.count()}")
        self.stdout.write(f"  Users:      {User.objects.count()}")
        self.stdout.write(f"  Orders:     {Order.objects.count()}")
        self.stdout.write(f"  OrderItems: {OrderItem.objects.count()}")
        self.stdout.write("")
        self.stdout.write(self.style.NOTICE(f"Default password for seeded users: {DEFAULT_PASSWORD!r}"))
