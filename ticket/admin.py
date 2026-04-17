from django.contrib import admin
from django.utils.html import format_html

from ticket.models import Appointment, AppointmentStatus, Feedback, Session, SessionStatus, StatusTypes, Ticket


# ─── Inlines ───────────────────────────────────────────────────────────────────

class TicketInline(admin.TabularInline):
    model  = Ticket
    extra  = 0
    fields = ('number', 'customer', 'status', 'is_vip', 'called_at', 'finished_at')
    readonly_fields = ('number', 'called_at', 'finished_at')
    show_change_link = True
    ordering = ('-is_vip', 'created_at')


# ─── Session ───────────────────────────────────────────────────────────────────

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display   = ('id', 'operator', 'service', 'date', 'status_badge', 'tickets_count')
    list_filter    = ('status', 'date', 'service__branch__business')
    search_fields  = ('operator__user__phone', 'service__title')
    readonly_fields = ('created_at', 'updated_at', 'started_at', 'closed_at', 'date')
    date_hierarchy = 'date'
    inlines        = [TicketInline]

    fieldsets = (
        ('Asosiy', {
            'fields': ('operator', 'service', 'date')
        }),
        ('Holat', {
            'fields': ('status',)
        }),
        ('Vaqtlar', {
            'fields': ('started_at', 'closed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            SessionStatus.ACTIVE: ('#16a34a', 'Faol'),
            SessionStatus.PAUSED: ('#d97706', 'Tanaffus'),
            SessionStatus.CLOSED: ('#dc2626', 'Yopildi'),
        }
        color, label = colors.get(obj.status, ('#6b7280', obj.status))
        return format_html('<span style="color:{};font-weight:500">● {}</span>', color, label)

    @admin.display(description='Chiptalar')
    def tickets_count(self, obj):
        total   = obj.tickets.count()
        waiting = obj.tickets.filter(status=StatusTypes.WAITING).count()
        done    = obj.tickets.filter(status=StatusTypes.DONE).count()
        return format_html(
            '<span>🎫 {} &nbsp;⏳ {} &nbsp;✅ {}</span>',
            total, waiting, done,
        )


# ─── Ticket ────────────────────────────────────────────────────────────────────

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display   = ('number', 'service', 'session', 'customer', 'status_badge', 'is_vip', 'wait_time', 'created_at')
    list_filter    = ('status', 'is_vip', 'service__branch__business')
    search_fields  = ('number', 'customer__phone')
    readonly_fields = ('number', 'called_at', 'served_at', 'finished_at', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Asosiy', {
            'fields': ('service', 'session', 'customer', 'number', 'is_vip')
        }),
        ('Holat', {
            'fields': ('status',)
        }),
        ('Vaqt kuzatuvi', {
            'fields': ('called_at', 'served_at', 'finished_at'),
        }),
        ('Tizim', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            StatusTypes.WAITING: ('#6b7280', 'Kutilmoqda'),
            StatusTypes.PROCESS: ('#2563eb', 'Jarayonda'),
            StatusTypes.DONE:    ('#16a34a', 'Bajarildi'),
            StatusTypes.CANCEL:  ('#dc2626', 'Bekor'),
            StatusTypes.SKIPPED: ('#d97706', "O'tkazib yuborildi"),
        }
        color, label = colors.get(obj.status, ('#6b7280', obj.status))
        return format_html('<span style="color:{};font-weight:500">● {}</span>', color, label)

    @admin.display(description='Kutish vaqti')
    def wait_time(self, obj):
        if obj.called_at and obj.created_at:
            mins = int((obj.called_at - obj.created_at).total_seconds() // 60)
            return f'{mins} daq'
        return '—'


# ─── Feedback ──────────────────────────────────────────────────────────────────

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display  = ('ticket', 'rating_stars', 'comment_short', 'created_at')
    list_filter   = ('rating', 'ticket__service__branch__business')
    search_fields = ('ticket__number', 'comment')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Baho')
    def rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)

    @admin.display(description='Izoh')
    def comment_short(self, obj):
        return obj.comment[:60] + '…' if len(obj.comment) > 60 else obj.comment or '—'


# ─── Appointment ───────────────────────────────────────────────────────────────

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display   = ('id', 'customer', 'time_slot', 'status_badge', 'created_at')
    list_filter    = ('status', 'time_slot__service__branch__business')
    search_fields  = ('customer__phone', 'time_slot__service__title')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            AppointmentStatus.PENDING:   ('#d97706', 'Kutilmoqda'),
            AppointmentStatus.CONFIRMED: ('#16a34a', 'Tasdiqlangan'),
            AppointmentStatus.CANCELLED: ('#dc2626', 'Bekor qilindi'),
            AppointmentStatus.COMPLETED: ('#2563eb', 'Bajarildi'),
            AppointmentStatus.NO_SHOW:   ('#6b7280', "Ko'rinmadi"),
        }
        color, label = colors.get(obj.status, ('#6b7280', obj.status))
        return format_html('<span style="color:{};font-weight:500">● {}</span>', color, label)
