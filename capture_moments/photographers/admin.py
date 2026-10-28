from django.contrib import admin

from .models import BlockedDate, Category, PhotographerProfile, PortfolioImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class PortfolioInline(admin.TabularInline):
    model = PortfolioImage
    extra = 0


@admin.register(PhotographerProfile)
class PhotographerProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "city", "price_per_hour", "experience_years", "is_active_listing")
    list_filter = ("is_active_listing", "city", "categories")
    search_fields = ("user__username", "user__first_name", "user__last_name", "city")
    inlines = [PortfolioInline]
    actions = ["hide_listings", "show_listings"]

    @admin.action(description="Hide selected from search")
    def hide_listings(self, request, queryset):
        queryset.update(is_active_listing=False)

    @admin.action(description="Show selected in search")
    def show_listings(self, request, queryset):
        queryset.update(is_active_listing=True)


@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display = ("profile", "date", "reason")
    list_filter = ("date",)
