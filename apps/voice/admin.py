from django.contrib import admin
from .models import VoiceLog, AIConversation


@admin.register(VoiceLog)
class VoiceLogAdmin(admin.ModelAdmin):
    list_display = ("user", "business", "short_transcript", "created_at")
    list_filter = ("business",)
    search_fields = ("transcript", "reply")
    readonly_fields = ("created_at",)

    def short_transcript(self, obj):
        return (obj.transcript[:60] + "...") if len(obj.transcript) > 60 else obj.transcript
    short_transcript.short_description = "متن"


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "short_content", "created_at")
    list_filter = ("role", "business")
    search_fields = ("content",)

    def short_content(self, obj):
        return (obj.content[:60] + "...") if len(obj.content) > 60 else obj.content
    short_content.short_description = "محتوا"