# Django E-Commerce Lite — Learning Plan

**Companion to:** `docs/DESIGN.md`
**Goal:** Use this project to build practical fluency with advanced Django, DRF, and Python patterns.
**How to use this doc:** Work through phases in order. Tick checkboxes as you complete tasks. Each phase ends with a self-check and a reflection prompt — write your answers in a short journal entry (a comment in this file works fine).

---

## How to learn effectively with this project

A few principles to keep in mind throughout:

1. **Write code yourself before reading the solution.** When the AI assistant offers to implement something, try it first. Then compare.
2. **Always inspect SQL.** Use `print(queryset.query)` or `django-debug-toolbar` to see what the ORM actually does. Magic you don't understand is technical debt.
3. **Read the official Django docs alongside the code.** Each phase below links to the relevant docs section.
4. **Commit per concept.** Small, focused commits with descriptive messages — they double as a learning log.
5. **Break things on purpose.** Delete a `select_related`, see the query count explode, then add it back. Understanding comes from contrast.
6. **Ask "why?"** Whenever a decision is made (e.g. `PROTECT` vs `CASCADE`), make sure you can articulate the reasoning before moving on.

---

## Progress overview

| Phase | Topic | Status |
|-------|-------|--------|
| 0 | Project setup | ✅ Complete |
| 1 | Models, admin, and migrations | ✅ Complete |
| 2 | ORM deep dive | ⬜ Not started |
| 3 | Serializers (DRF) | ⬜ Not started |
| 4 | Views, viewsets, and routing | ⬜ Not started |
| 5 | Authentication, permissions, signals | ⬜ Not started |
| 6 | Transactions, caching, optimisation | ⬜ Not started |
| 7 | Testing | ⬜ Not started |
| 8 | Python practices and code quality | ⬜ Not started |

---

## Phase 0 — Project setup ✅

**Status:** Complete.

What was done:

- [x] Created project folder `~/django-ecommerce-lite` with git
- [x] Python 3.13 virtual environment
- [x] Installed Django 6, DRF, django-filter, drf-spectacular
- [x] `config/` project package and `shop/` app scaffolded
- [x] `requirements.txt` and `.gitignore` committed
- [x] Branches: `develop` (base) and `feature/shop-lite-app-setup` (current)

**Run locally:**

```bash
cd ~/django-ecommerce-lite
source .venv/bin/activate
python manage.py runserver
```

---

## Phase 1 — Models, admin, and migrations ✅

**Status:** Complete.

What was done:

- [x] Five domain models: `Category`, `Product`, `Inventory`, `Order`, `OrderItem`
- [x] Docstrings on each model explaining purpose and design choices
- [x] Admin registration for all models with inlines and autocomplete
- [x] Single `0001_initial` migration applied

**Concepts you've now touched:**

- `CharField`, `SlugField`, `TextField`, `DecimalField`, `PositiveIntegerField`, `DateTimeField`
- `ForeignKey`, `OneToOneField`, self-referential FK
- `on_delete` (CASCADE vs PROTECT)
- `Meta`: `ordering`, `verbose_name_plural`, `UniqueConstraint`
- `TextChoices` for status enums
- `auto_now_add` vs `auto_now`
- `@property` for computed fields (`total`, `line_total`, `is_low_stock`)
- `save()` override (slug generation, `unit_price` snapshot)
- `settings.AUTH_USER_MODEL`
- Django Admin: `ModelAdmin`, `StackedInline`, `TabularInline`, `prepopulated_fields`, `autocomplete_fields`, `@admin.display`

**Reflection prompts:**

1. Why is `OrderItem.unit_price` a snapshot field instead of always reading `Product.price`?
2. Why does `Product.category` use `PROTECT` but `OrderItem.order` uses `CASCADE`?
3. What does `related_name="items"` on `OrderItem.order` actually let you do?

---

## Phase 2 — ORM deep dive ⬜

**Goal:** Stop thinking in tables and start thinking in querysets. Be able to predict the SQL Django generates.

**Docs:** [Making queries](https://docs.djangoproject.com/en/stable/topics/db/queries/) · [QuerySet API reference](https://docs.djangoproject.com/en/stable/ref/models/querysets/) · [Aggregation](https://docs.djangoproject.com/en/stable/topics/db/aggregation/)

### Setup tasks

- [x] Create a `manage.py` command (or shell script) that seeds the database with sample data:
  - 3 top-level categories with 1–2 subcategories each
  - 10 products across categories
  - `Inventory` row per product
  - 1 superuser + 2 regular users
  - 5 orders with varying numbers of items
  - Implemented as `python manage.py seed_data [--flush] [--orders N] [--seed N]`
- [ ] Install `django-debug-toolbar` (or use `python manage.py shell_plus --print-sql` via django-extensions)

### Core exercises

Work through each in `manage.py shell`. For each query, **inspect the SQL** with `print(qs.query)`.

- [ ] **`select_related`** — fetch all products with their categories in one query (vs N+1 without it)
- [ ] **`prefetch_related`** — fetch all orders with their items and each item's product
- [ ] **`annotate` + `Sum`** — compute order totals in SQL, not Python
- [ ] **`aggregate`** — total revenue across all orders
- [ ] **`F` expressions** — find inventory rows where `quantity <= low_stock_threshold` without loading rows into Python
- [ ] **`Q` objects** — find products that are either under $50 OR in the "Sale" category
- [ ] **Subquery** — find products that have never been ordered
- [ ] **`values()` / `values_list()`** — get just product names and prices, not full objects
- [ ] **`only()` / `defer()`** — fetch only specific columns from a model

### Advanced exercises

- [ ] **Custom manager**: add an `ActiveProductManager` so `Product.active.all()` returns only `is_active=True` products
- [ ] **Custom QuerySet method**: add `.in_stock()` chainable to the product manager
- [ ] **Fix the `Order.total` N+1** (see §5.1 of DESIGN.md) by annotating the queryset with a `Sum` of `F("items__quantity") * F("items__unit_price")`

### Self-check

You should be able to answer:

1. What's the difference between `select_related` and `prefetch_related`? When does each apply?
2. Why does `Product.objects.filter(is_active=True).count()` issue only one query, but iterating over `Order.objects.all()` and accessing `.total` issues many?
3. What's the difference between `Manager` and `QuerySet`? Why would you customise both?

### Reflection prompt

Pick one query you optimised. Write down the query count before and after, and one sentence explaining why the change worked.

---

## Phase 3 — Serializers (DRF) ⬜

**Goal:** Translate between Django models and JSON correctly, with validation that catches bad input before it reaches the database.

**Docs:** [DRF serializers](https://www.django-rest-framework.org/api-guide/serializers/) · [DRF validators](https://www.django-rest-framework.org/api-guide/validators/)

### Tasks

Create `shop/serializers.py`.

- [ ] `CategorySerializer` — `ModelSerializer` over `Category`
- [ ] `InventorySerializer` — read-only, includes `is_low_stock`
- [ ] `ProductListSerializer` — flat representation for the list view
- [ ] `ProductDetailSerializer` — nested `category` and `inventory`
- [ ] `OrderItemSerializer` — write `product` by id, expose `unit_price` and `line_total` read-only
- [ ] `OrderReadSerializer` — nested items, `total` via `SerializerMethodField`
- [ ] `OrderWriteSerializer` — nested create: one POST creates `Order` + N `OrderItem` rows in one go
- [ ] Field-level validator: `quantity` must be ≥ 1
- [ ] Object-level validator on `OrderWriteSerializer`: every requested item must have sufficient inventory

### Self-check

1. Why split `ProductListSerializer` and `ProductDetailSerializer`?
2. What is the difference between `validate_<fieldname>()` and `validate()`?
3. How does `create()` on a serializer differ from `create()` on a manager?

### Reflection prompt

When would you choose `SerializerMethodField` over a model `@property`? Both work — what trade-offs are involved?

---

## Phase 4 — Views, viewsets, and routing ⬜

**Goal:** Build a working REST API. Move from low-level to high-level abstractions and understand what each layer gives you.

**Docs:** [DRF generic views](https://www.django-rest-framework.org/api-guide/generic-views/) · [ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/) · [Routers](https://www.django-rest-framework.org/api-guide/routers/) · [django-filter integration](https://www.django-rest-framework.org/api-guide/filtering/#djangofilterbackend)

### Tasks (progressive)

Build in `shop/views.py` and `shop/urls.py`.

- [ ] **Step 1 — `APIView`**: implement `ProductListView` with manual `get()` returning JSON
- [ ] **Step 2 — Generic view**: replace with `ListAPIView` using `ProductListSerializer`
- [ ] **Step 3 — Detail view**: `RetrieveAPIView` keyed by `slug` (not `pk`)
- [ ] **Step 4 — Filtering**: add `DjangoFilterBackend` with `filterset_fields = ["category", "is_active"]`
- [ ] **Step 5 — Custom filterset**: build a `ProductFilter` class with `min_price`, `max_price`, `category__slug`
- [ ] **Step 6 — ViewSet + Router**: replace `ProductListView` + `ProductDetailView` with a single `ProductViewSet`
- [ ] **Step 7 — Custom action**: add `@action(detail=True, methods=["post"]) def checkout()` on `OrderViewSet`
- [ ] **Step 8 — Pagination**: enable `PageNumberPagination` globally in settings

### Self-check

1. What does `DefaultRouter` actually generate? List the URLs for a registered viewset.
2. When would you prefer a `ViewSet` over a `ModelViewSet`?
3. How does DRF resolve which serializer to use? How would you use a different serializer for list vs detail?

### Reflection prompt

Compare the line count and clarity of your Step 1 implementation vs the Step 6 ViewSet version. What did you give up by going higher-level?

---

## Phase 5 — Authentication, permissions, and signals ⬜

**Goal:** Secure the API. Wire up cross-cutting concerns (inventory updates) without coupling them to views.

**Docs:** [DRF authentication](https://www.django-rest-framework.org/api-guide/authentication/) · [DRF permissions](https://www.django-rest-framework.org/api-guide/permissions/) · [Django signals](https://docs.djangoproject.com/en/stable/topics/signals/)

### Authentication

- [ ] Install `djangorestframework-simplejwt`
- [ ] Configure JWT in `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]`
- [ ] Add `/api/auth/token/` and `/api/auth/token/refresh/` endpoints
- [ ] Verify with `curl` that you can obtain a token and call a protected endpoint

### Permissions

- [ ] Apply `IsAuthenticated` to `OrderViewSet`
- [ ] Write `IsOwnerOrAdmin` permission class in `shop/permissions.py`
- [ ] Override `get_queryset()` so non-admins only see their own orders
- [ ] Verify a non-owner gets `403 Forbidden`

### Signals

- [ ] Create `shop/signals.py`
- [ ] Connect signals in `ShopConfig.ready()` (and add `default_app_config` if needed)
- [ ] **Signal 1:** `post_save` on `Product` → auto-create `Inventory(product=instance, quantity=0)` on first save
- [ ] **Signal 2:** `post_save` on `OrderItem` → decrement `Inventory.quantity` by `instance.quantity`
- [ ] Add safety: don't go negative, raise instead

### Self-check

1. Why connect signals in `ready()` rather than at module top level?
2. What's the difference between `permission_classes` on a view and overriding `get_queryset()`? Do you need both?
3. What happens if a signal handler raises an exception inside a `transaction.atomic()` block?

### Reflection prompt

Signals are powerful but easy to abuse. Name one alternative to a signal for the inventory decrement (a service function?). What are the trade-offs?

---

## Phase 6 — Transactions, caching, and optimisation ⬜

**Goal:** Make the API correct under concurrency and fast under load.

**Docs:** [Database transactions](https://docs.djangoproject.com/en/stable/topics/db/transactions/) · [Django's cache framework](https://docs.djangoproject.com/en/stable/topics/cache/) · [Database optimisation](https://docs.djangoproject.com/en/stable/topics/db/optimization/)

### Transactions

- [ ] Wrap order creation in `transaction.atomic()`
- [ ] Write a test that triggers a validation error mid-creation and verifies no partial order is persisted
- [ ] Use `select_for_update()` on inventory rows during checkout to prevent overselling

### Caching

- [ ] Configure a `LocMemCache` backend in settings (good enough for dev)
- [ ] Add `@cache_page(60 * 5)` to the product list view; verify with debug toolbar that subsequent calls don't hit the DB
- [ ] Use low-level `cache.get()` / `cache.set()` to cache the category tree
- [ ] Invalidate the cache on `Product.save()` (signal or override)

### Optimisation

- [ ] Install `django-debug-toolbar`
- [ ] List the order index page, note query count
- [ ] Add `prefetch_related("items__product")` to the viewset's `get_queryset()`
- [ ] Re-measure — document the improvement
- [ ] Use `only()` to fetch only fields the serializer actually needs

### Self-check

1. What's the difference between `transaction.atomic()` as a decorator vs context manager?
2. When does `cache_page` _not_ work, and why?
3. What's the danger of caching a queryset directly vs caching serialised data?

### Reflection prompt

Measure one endpoint's response time before and after optimisation. What was the dominant cost — query count, payload size, serialisation?

---

## Phase 7 — Testing ⬜

**Goal:** Build a test suite that gives you confidence to refactor.

**Docs:** [Django testing](https://docs.djangoproject.com/en/stable/topics/testing/) · [DRF testing](https://www.django-rest-framework.org/api-guide/testing/)

### Tasks

- [ ] Move `tests.py` to a `tests/` package
- [ ] Install `factory-boy`; create `tests/factories.py` with factories for each model
- [ ] **Model tests** (`tests/test_models.py`):
  - [ ] `Category.save()` generates slug from name when blank
  - [ ] `OrderItem.save()` snapshots `Product.price` into `unit_price`
  - [ ] `Order.total` matches sum of line totals
  - [ ] `Inventory.is_low_stock` boundary conditions
- [ ] **API tests** (`tests/test_api.py`):
  - [ ] `GET /api/products/` returns active products only
  - [ ] `POST /api/orders/` creates order + items, decrements inventory
  - [ ] `POST /api/orders/` with insufficient stock returns 400 and persists nothing
  - [ ] `GET /api/orders/{id}/` returns 403 for non-owner
- [ ] **Permission tests**: every protected endpoint, every actor combination
- [ ] Set up `pytest-django` (optional) and measure coverage with `coverage.py`

### Self-check

1. Why use `APITestCase` instead of `TestCase` for API tests?
2. When should you use `setUpTestData` vs `setUp`?
3. What's wrong with hitting the network or filesystem from a unit test?

### Reflection prompt

Find a bug deliberately. Add a test that fails. Fix the code. Confirm the test passes. Was the test easy or hard to write? What does that tell you about your code's design?

---

## Phase 8 — Python practices and code quality ⬜

**Goal:** Code you'd be happy to show in a code review.

### Tasks

- [ ] Add type hints to all function and method signatures
- [ ] Add `default_auto_field = "django.db.models.BigAutoField"` to `ShopConfig`
- [ ] Extract complex business logic from views into `shop/services.py` (e.g. `checkout_order(order)`)
- [ ] Run `ruff` (or `flake8` + `black` + `isort`) and fix all warnings
- [ ] Run `mypy` with `django-stubs` and resolve issues
- [ ] Review every docstring — does it explain the _why_, not just the _what_?
- [ ] Add a `pre-commit` config that runs `ruff` and `mypy` on commit
- [ ] Set up GitHub Actions (or just a local script) that runs the test suite

### Self-check

1. Where should business logic live: model, manager, serializer, view, or service?
2. What's the difference between a `@property` and a method? When would you choose each?
3. Why prefer `dataclass` or `TypedDict` over plain dicts for structured data passed between functions?

### Reflection prompt

Look back at code you wrote in Phase 3 or 4. Refactor one thing using what you've learned. Note what changed and why.

---

## Capstone ideas (after Phase 8)

Once the roadmap is complete, pick one to deepen specific skills:

- **Tags + faceted search** — exercise M2M relations and complex filtering
- **Stripe integration** — webhooks, idempotency, external API patterns
- **Background tasks with Celery** — send order confirmation emails async
- **Switch to PostgreSQL + full-text search** — `SearchVector`, `SearchRank`
- **GraphQL layer with Strawberry** — compare against DRF
- **Multi-tenant support** — separate stores per `Site`

---

## Recommended reading alongside the project

- **Two Scoops of Django** — best-practice cookbook
- **Django for APIs** by William S. Vincent — short and DRF-focused
- **High Performance Django** — older but still relevant for caching and query patterns
- **Official Django docs** — actually read the topic guides cover-to-cover; they're excellent

---

## Working log

Keep a running journal at the bottom of this file. Format suggestion:

```
### 2026-05-XX — Phase 2: select_related
- Practised select_related on Product.category
- Query count dropped from 11 to 1 for a 10-product list
- Surprised by: print(qs.query) showed a LEFT OUTER JOIN, not INNER
```

Start writing:

---
