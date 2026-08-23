from django.contrib import admin

from .models import AnswerAlias, Composer, Part, Recording, Work


@admin.register(Composer)
class ComposerAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("name", "owner")
    search_fields = ("name",)


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("title", "composer", "kind", "archived")
    list_filter = ("kind", "archived")
    search_fields = ("title", "composer__name")


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("display_name", "work", "duration_ms", "status", "archived")
    list_filter = ("status", "archived")


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("title", "recording", "start_ms", "end_ms", "archived")
    list_filter = ("archived",)


admin.site.register(AnswerAlias)
