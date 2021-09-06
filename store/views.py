from django.shortcuts import render
from .models import *
from django.http import JsonResponse
import json
import datetime
from django.db.models import F

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from . utils import cookieCart, cartData, guestOrder
# Create your views here.

def store(request):
    data= cartData(request)

    cartItems=data['cartItems']
    
       
    products= Product.objects.all()
    context={'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)
    
def cart(request):
    data=cartData(request)
    cartItems=data['cartItems']
    order=data['order']
    items=data['items']

    context={'items':  items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)

def checkout(request):
    data=cartData(request)
    cartItems=data['cartItems']
    order=data['order']
    items=data['items']

    context={'items':items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)

def auth(request):
    data= json.loads(request.body)
    uname= data['email']
    password = data['password']
    user = authenticate(username= uname, password=password)
    if user is not None:
        login(request, user)
        

    else:
        user = User.objects.create_user(username= uname, password=password, email='email@gmail.com')
        user.save()
        customer, created = Customer.objects.get_or_create(
            user= user ,
            name= uname,
            email = 'email@gmail.com'

            )     
        customer.save()
        login(request, user)
    
    return JsonResponse('ok', safe=False) 

@login_required
def loggingOut(request):
    logout(request)  
    data=cartData(request)
    cartItems=data['cartItems']
    order=data['order']
    items=data['items']

    context={'items':items, 'order': order, 'cartItems': cartItems}
    return JsonResponse('user logged out', safe=False) 


def updateItem(request):
    #parse the data returned from the fetch
   
    data= json.loads(request.body)
    productId=data['productId']
    action= data['action']

    print('Action:', action)
    print('Product id:', productId)
    customer = request.user.customer
    product= Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    #print(order.get_cart_items)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
   
    if action=='add':
        orderItem.quantity= (orderItem.quantity + 1)
    elif action=='remove':
        orderItem.quantity= (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity<=0:
        orderItem.delete()
    
    
    return JsonResponse('item was added', safe=False)
#this shit***********

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)


    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

    else:
        customer, order = guestOrder(request, data)
             
    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAdress.objects.create(
        customer=customer,
        order=order,
        address=data['shipping']['address'],
        city=data['shipping']['city'],
        state=data['shipping']['state'],
        zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment submitted..', safe=False)