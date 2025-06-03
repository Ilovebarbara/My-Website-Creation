from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'featured')
    list_filter = ('featured', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
