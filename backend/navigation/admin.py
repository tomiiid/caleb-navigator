from django.contrib import admin
from .models import Building, Waypoint, Edge, NavigationLog


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'latitude', 'longitude', 'is_active']
    list_filter = ['category', 'is_active', 'is_accessible']
    search_fields = ['name', 'short_name']


@admin.register(Waypoint)
class WaypointAdmin(admin.ModelAdmin):
    list_display = ['name', 'waypoint_type', 'building', 'latitude', 'longitude', 'is_active']
    list_filter = ['waypoint_type', 'is_active']
    search_fields = ['name']


@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    list_display = ['from_waypoint', 'to_waypoint', 'distance', 'surface', 'is_accessible', 'is_active']
    list_filter = ['surface', 'is_accessible', 'is_active']


@admin.register(NavigationLog)
class NavigationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'origin', 'destination', 'timestamp', 'was_successful']
    list_filter = ['was_successful']
    readonly_fields = ['user', 'origin', 'destination', 'timestamp', 'was_successful']