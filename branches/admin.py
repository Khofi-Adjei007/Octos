# branches/admin.py
from django.contrib import admin
from .models import (
    Country, Region, City, District, Location,Branch
)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'currency', 'timezone', 'created_at')
    search_fields = ('name', 'code')
    ordering = ('name',)

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'created_at')
    search_fields = ('name', 'country__name')
    list_filter = ('country',)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'code', 'created_at')
    search_fields = ('name', 'region__name')

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'code', 'created_at')
    search_fields = ('name', 'city__name')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'code', 'parent', 'is_active', 'created_at')
    search_fields = ('name', 'type', 'code')
    list_filter = ('type', 'is_active')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'country', 'region', 'city', 'is_active', 'is_main')
    search_fields = ('name', 'code', 'manager__employee_email', 'contact_person')
    list_filter = ('country', 'region', 'is_active', 'is_main')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    ordering = ('name',)
