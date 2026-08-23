from django.contrib import admin

from .models import ReviewLog, ReviewSession, StudyState


@admin.register(StudyState)
class StudyStateAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("part", "due_at", "challenge_level", "frontier_ms", "review_count")


@admin.register(ReviewSession)
class ReviewSessionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("public_id", "stage", "created_at", "expires_at")
    readonly_fields = ("public_id", "created_at", "revealed_at", "completed_at")


@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("part", "rating", "answer_accepted", "reviewed_at")
    readonly_fields = [field.name for field in ReviewLog._meta.fields]

    def has_add_permission(self, request: object) -> bool:
        return False

    def has_change_permission(self, request: object, obj: object | None = None) -> bool:
        return False

    def has_delete_permission(self, request: object, obj: object | None = None) -> bool:
        return False
