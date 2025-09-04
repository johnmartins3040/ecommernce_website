
from .import views 
from django.urls import path
from django .conf import settings
from django.conf.urls.static import static

urlpatterns = [
  # path('base/',views.base, name='base'),
  path('',views.home, name='home'),
  path('category/<slug:slug>/',views.product_list, name='category_products'),
  path('best-sellers/', views.product_list, {'section': 'best_sellers'}, name='best_sellers'),
  path('gift-ideas/', views.product_list, {'section': 'gift_ideas'}, name='gift_ideas'),
  path('new-releases/', views.product_list, {'section': 'new_releases'}, name='new_releases'),
  path('todays-deals/', views.product_list, {'section': 'todays_deals'}, name='todays_deals'),
  path('product/<slug:slug>/', views.product_detail, name='product_detail'),
  path('customer_care/', views.customer_care, name='customer_care'),
  path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
  path('cart/', views.cart_view, name='cart_view'),
  path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
  path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
  path("checkout/", views.checkout, name="checkout"),
  path("paystack/callback/", views.paystack_callback, name="paystack_callback"),
  path("stripe-checkout/<int:order_id>/", views.stripe_checkout, name="stripe_checkout"),
  path("success/", views.success, name="success"),
  path("cancel/", views.cancel, name="cancel"),
]

if settings.DEBUG:
  urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)