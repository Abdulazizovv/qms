from django.contrib import admin
from django.utils.html import format_html
from ticket.models import Session, Ticket, SessionStatus, StatusTypes as TicketStatus


# ─── Inlines ───────────────────────────────────────────────────────────────

class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    fields = ("number", "customer", "status", "is_vip", "called_at", "served_at", "finished_at")
    readonly_fields = ("number", "called_at", "served_at", "finished_at")
    show_change_link = True
    ordering = ("-is_vip", "created_at")


# ─── Session ───────────────────────────────────────────────────────────────

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display  = ("id", "operator", "service", "date", "status_badge", "tickets_count", "current_ticket")
    list_filter   = ("status", "date", "service__branch__business")
    search_fields = ("operator__user__phone", "service__title")
    readonly_fields = ("created_at", "updated_at", "started_at", "closed_at")
    date_hierarchy  = "date"
    inlines = [TicketInline]

    fieldsets = (
        ("Asosiy", {
            "fields": ("operator", "service", "date")
        }),
        ("Holat", {
            "fields": ("status", "current_ticket")
        }),
        ("Vaqtlar", {
            "fields": ("started_at", "closed_at", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            SessionStatus.PENDING: ("#6b7280", "Kutilmoqda"),
            SessionStatus.ACTIVE:  ("#16a34a", "Faol"),
            SessionStatus.PAUSED:  ("#d97706", "Tanaffus"),
            SessionStatus.CLOSED:  ("#dc2626", "Yopildi"),
        }
        color, label = colors.get(obj.status, ("#6b7280", obj.status))
        return format_html('<span style="color:{};font-weight:500">● {}</span>', color, label)

    @admin.display(description="Chiptalar")
    def tickets_count(self, obj):
        total   = obj.tickets.count()
        waiting = obj.tickets.filter(status=TicketStatus.WAITING).count()
        done    = obj.tickets.filter(status=TicketStatus.DONE).count()
        return format_html(
            '<span title="Jami / Kutmoqda / Bajarildi">'
            '🎫 {} &nbsp;⏳ {} &nbsp;✅ {}'
            '</span>',
            total, waiting, done
        )


# ─── Ticket ────────────────────────────────────────────────────────────────

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display  = ("number", "session", "customer", "status_badge", "is_vip", "wait_time", "created_at")
    list_filter   = ("status", "is_vip", "session__date", "session__service__branch__business")
    search_fields = ("number", "customer__phone")
    readonly_fields = ("number", "called_at", "served_at", "finished_at", "created_at", "updated_at")
    date_hierarchy  = "created_at"

    fieldsets = (
        ("Asosiy", {
            "fields": ("session", "customer", "number", "is_vip")
        }),
        ("Holat", {
            "fields": ("status",)
        }),
        ("Vaqt kuzatuvi", {
            "fields": ("called_at", "served_at", "finished_at"),
        }),
        ("Tizim", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            TicketStatus.WAITING: ("#6b7280", "Kutilmoqda"),
            TicketStatus.PROCESS: ("#2563eb", "Jarayonda"),
            TicketStatus.DONE:    ("#16a34a", "Bajarildi"),
            TicketStatus.CANCEL:  ("#dc2626", "Bekor"),
            TicketStatus.SKIPPED: ("#d97706", "O'tkazib yuborildi"),
        }
        color, label = colors.get(obj.status, ("#6b7280", obj.status))
        return format_html('<span style="color:{};font-weight:500">● {}</span>', color, label)

    @admin.display(description="Kutish vaqti")
    def wait_time(self, obj):
        if obj.called_at and obj.created_at:
            delta = obj.called_at - obj.created_at
            mins = int(delta.total_seconds() // 60)
            return f"{mins} daq"
        return "—"