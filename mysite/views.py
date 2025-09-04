from django.shortcuts import render,get_object_or_404,redirect
from mysite.models import Category, Product, Cart, CartItem,Order, OrderItem
import stripe
import requests
from django.conf import settings

# Create your views here.

def base(request):
    categories = Category.objects.all()
    return render(request, 'base.html', {'categories': categories})

def home(request):

  categories = Category.objects.all()

  category_products = {}

  for category in categories:
        # take only 10 items from each category
     category_products[category] = Product.objects.filter(category=category)[:10]

  query = request.GET.get('q')

  if query:
        # search inside all categories
        for category in categories:
            category.search_products = category.products.filter(name__icontains=query)
  else:
        for category in categories:
            category.search_products = category.products.all()

  context ={
    "categories":categories,
    "query": query,
  }

  return render(request,'index.html',context)


def product_list(request, slug=None, section=None):
    products = []
    title = ""
    query = request.GET.get('q')

    # --- Normal categories ---
    if slug:
        category = get_object_or_404(Category, slug=slug)
        if query:
            products = category.products.filter(name__icontains=query)
        else:
            products = category.products.all()
        title = category.name

    # --- Special sections ---
    elif section == 'best_sellers':
        products = Product.objects.order_by('-sales')[:20]
        title = "Best Sellers"

    elif section == 'gift_ideas':
        products = Product.objects.filter(is_gift=True)
        title = "Gift Ideas"

    elif section == 'new_releases':
        products = Product.objects.order_by('-created')[:20]
        title = "New Releases"

    elif section == 'todays_deals':
        products = Product.objects.filter(discount_price__isnull=False)
        title = "Today's Deals"
        

    context = {
        'title': title,
        'products': products
    }
    return render(request, "category.html", context)


def customer_care(request):
    
    return render(request, "customer_care.html")



def product_detail(request, slug):
   product = get_object_or_404(Product, slug=slug)
   return render(request, 'single_page.html', {'product': product})


def get_user_cart(request):
    # For logged-in users, get or create their cart
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        # For guests, you can extend this later (session-based cart)
        return None

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_user_cart(request)

     # Save the previous page to session
    request.session['last_product_page'] = request.META.get('HTTP_REFERER', '/')

    if not cart:
        # For guests, redirect or handle session cart here
        return redirect('product_detail', slug=product.slug)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart_view')

def cart_view(request):
    cart = get_user_cart(request)
    if not cart:
        # For guests, show empty cart or handle session cart
        return render(request, 'cart.html', {'products': [], 'total': 0})

    items = cart.items.select_related('product').all()
    total = cart.total_price()
    return render(request, 'cart.html', {'items': items, 'total': total})

def remove_from_cart(request, item_id):
    cart = get_user_cart(request)
    if not cart:
        return redirect('cart_view')

    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return redirect('cart_view')

def update_cart_item(request, item_id):
    cart = get_user_cart(request)
    if not cart:
        return redirect('cart_view')

    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        item.quantity = quantity
        item.save()
    else:
        item.delete()
    return redirect('cart_view')

# checkout
def checkout(request):
    cart = get_user_cart(request)
    if not cart or not cart.items.exists():
        return redirect('cart_view')

    total = cart.total_price()
    order = Order.objects.create(user=request.user, total_amount=total)
    for item in cart.items.all():
        OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)

    context = {
        "order": order,
        "paystack_public_key": settings.PAYSTACK_PUBLIC_KEY,
        "stripe_public_key": getattr(settings, "STRIPE_PUBLISHABLE_KEY", ""),  # may be ""
    }
    return render(request, "checkout.html", context)



# Paystack Callback
def paystack_callback(request):
    reference = request.GET.get("reference")
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    response = requests.get(url, headers=headers)
    res = response.json()

    if res.get("status") and res["data"]["status"] == "success":
        order = Order.objects.filter(user=request.user).last()
        order.paid = True
        order.save()
        return render(request, "success.html", {"order": order})
    else:
        return render(request, "checkout_message.html", {"error": res})
    


# Stripe Checkout
def stripe_checkout(request, order_id):
    stripe_secret = getattr(settings, "STRIPE_SECRET_KEY", "")
    if not stripe_secret:
        return render(
            request,
            "checkout_message.html",
            {"error": "Stripe is not configured yet. Add STRIPE_SECRET_KEY in settings.py to enable global payments."},
        )

    stripe.api_key = stripe_secret
    order = get_object_or_404(Order, id=order_id, user=request.user)

    try:
        order_items_qs = order.items.all()
    except AttributeError:
        order_items_qs = order.orderitem_set.all()

    if not order_items_qs.exists():
        return render(request, "checkout_message.html", {"error": "Order has no items."})

    line_items = []
    for item in order_items_qs:
        unit_amount_cents = int(Decimal(item.product.price) * 100)
        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {"name": item.product.name},
                "unit_amount": unit_amount_cents,
            },
            "quantity": item.quantity,
        })

    success_url = request.build_absolute_uri(reverse("success")) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse("cancel"))

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return redirect(session.url, code=303)


# ✅ Updated success view goes here
def success(request):
    stripe_secret = getattr(settings, "STRIPE_SECRET_KEY", "")
    stripe.api_key = stripe_secret

    session_id = request.GET.get("session_id")
    if not session_id:
        return render(request, "checkout_message.html", {
            "title": "⚠️ Missing Session",
            "message": "Stripe session ID not found. Payment could not be verified."
        })

    # Get the checkout session from Stripe
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status == "paid":
        # Find the latest unpaid order for the user
        order = Order.objects.filter(user=request.user, paid=False).last()
        if order:
            order.paid = True
            order.save()

        return render(request, "checkout_message.html", {
            "title": "✅ Payment Successful",
            "message": "Thank you! Your order has been placed successfully.",
            "order": order,
        })
    else:
        return render(request, "checkout_message.html", {
            "title": "⚠️ Payment Not Verified",
            "message": "Stripe did not confirm the payment. Please try again."
        })


def cancel(request):
    return render(request, "checkout_message.html", {
        "title": "⚠️ Payment Cancelled",
        "message": "Your payment was cancelled. You can try again anytime."
    })

