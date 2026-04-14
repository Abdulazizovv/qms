from django.contrib import admin

from django.utils.html import format_html
from business.models import Business, Branch, WorkingDay, Service, Operator


# ─── Inlines ───────────────────────────────────────────────────────────────

class WorkingDayInline(admin.TabularInline):
    model = WorkingDay
    extra = 0
    fields = ("day", "open_time", "close_time", "break_start", "break_end")


class BranchInline(admin.TabularInline):
    model = Branch
    extra = 0
    fields = ("title", "location", "is_active")
    show_change_link = True


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0
    fields = ("title", "ticket_prefix", "estimated_time_minutes", "price", "status")
    show_change_link = True


class OperatorInline(admin.TabularInline):
    model = Operator
    extra = 0
    fields = ("user", "desk_number", "is_active")
    show_change_link = True


# ─── Business ──────────────────────────────────────────────────────────────

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display  = ("title", "owner", "logo_preview", "created_at")
    list_filter   = ("created_at",)
    search_fields = ("title", "owner__phone")
    readonly_fields = ("logo_preview", "created_at", "updated_at")
    inlines = [BranchInline]

    fieldsets = (
        ("Asosiy", {
            "fields": ("owner", "title", "about")
        }),
        ("Logo", {
            "fields": ("logo", "logo_preview")
        }),
        ("Vaqtlar", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Logo")
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="height:40px;border-radius:6px"/>', obj.logo.url)
        return "—"


# ─── Branch ────────────────────────────────────────────────────────────────

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display  = ("title", "business", "location", "is_active_badge", "created_at")
    list_filter   = ("is_active", "business")
    search_fields = ("title", "location", "business__title")
    readonly_fields = ("created_at", "updated_at")
    inlines = [WorkingDayInline, ServiceInline, OperatorInline]

    fieldsets = (
        ("Asosiy", {
            "fields": ("business", "title", "description", "location")
        }),
        ("Holat", {
            "fields": ("is_active",)
        }),
        ("Vaqtlar", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Holat", boolean=False)
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#16a34a;font-weight:500">● Faol</span>')
        return format_html('<span style="color:#dc2626;font-weight:500">● Nofaol</span>')


# ─── Service ───────────────────────────────────────────────────────────────

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display  = ("title", "branch", "ticket_prefix", "estimated_time_minutes", "price_display", "status_badge")
    list_filter   = ("status", "branch__business")
    search_fields = ("title", "branch__title")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Asosiy", {
            "fields": ("branch", "title", "description", "requirements")
        }),
        ("Sozlamalar", {
            "fields": ("ticket_prefix", "estimated_time_minutes", "price", "status")
        }),
        ("Vaqtlar", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Narx")
    def price_display(self, obj):
        return f"{obj.price:,} so'm".replace(",", " ")

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "active":   ("#16a34a", "Faol"),
            "break":    ("#d97706", "Tanaffus"),
            "inactive": ("#dc2626", "Nofaol"),
        }
        color, label = colors.get(obj.status, ("#6b7280", obj.status))
        return format_html('<span style="color:{};font-weight:500">● {}</span>', color, label)




@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display  = ("user", "branch", "desk_number", "services_list", "is_active_badge")
    list_filter   = ("is_active", "branch__business")
    search_fields = ("user__phone", "desk_number", "branch__title")
    filter_horizontal = ("services",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Asosiy", {
            "fields": ("user", "branch", "desk_number")
        }),
        ("Xizmatlar", {
            "fields": ("services",)
        }),
        ("Holat", {
            "fields": ("is_active",)
        }),
        ("Vaqtlar", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Xizmatlar")
    def services_list(self, obj):
        names = obj.services.values_list("title", flat=True)[:3]
        result = ", ".join(names)
        total = obj.services.count()
        if total > 3:
            result += f" (+{total - 3})"
        return result or "—"

    @admin.display(description="Holat")
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#16a34a;font-weight:500">● Faol</span>')
        return format_html('<span style="color:#dc2626;font-weight:500">● Nofaol</span>')
from business.models import Business, Service, Branch, Operator



# admin.site.register(Business)
# admin.site.register(Service)
# admin.site.register(Branch)
# admin.site.register(Operator)

