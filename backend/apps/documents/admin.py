from django.contrib import admin

from apps.documents.models import Document, DocumentCategory


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("minio_object_key", "category", "is_confidential", "target")
    list_filter = ("is_confidential",)
