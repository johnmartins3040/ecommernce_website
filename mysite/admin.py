from django.contrib import admin
from django.utils.html import format_html
from .models import Category,Product,Cart,CartItem,Order,OrderItem

# Register your models here.

class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "image_tag", "price")   # shows columns in admin list
    readonly_fields = ("image_tag",)                # makes preview visible in detail page

    def image_tag(self, obj):
        if obj.image:  # check if product has an image
            return format_html(
                '<img src="{}" width="80" height="80" style="object-fit:cover; border-radius:5px;" />',
                obj.image.url
            )
        return "No Image"
    image_tag.short_description = "Image Preview"


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "product_image")

    def product_image(self, obj):
        if obj.product and obj.product.image:
            return format_html('<img src="{}" width="60" height="60" style="object-fit: cover; border-radius: 5px;" />', obj.product.image.url)
        return "No Image"
    product_image.short_description = "Product Image"


class cartitemAdmin(admin.ModelAdmin):
    list_display = ( "product", "quantity", "product_image")

    def product_image(self, obj):
        if obj.product and obj.product.image:
            return format_html('<img src="{}" width="60" height="60" style="object-fit: cover; border-radius: 5px;" />', obj.product.image.url)
        return "No Image"
    product_image.short_description = "Product Image"

 




admin.site.register(Product,ProductAdmin)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(CartItem,cartitemAdmin)
admin.site.register(Order)
admin.site.register(OrderItem,OrderItemAdmin)