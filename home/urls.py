from django.contrib import admin
from django.urls import path,include
from home import views
urlpatterns = [
    path('', views.signIn),
    path('signUp/', views.signUp, name="signup"),
    path('logout/', views.logout, name="log"),
    path('reset/', views.reset),
    path('home/',views.home),
    path('index/',views.index),
    path('upload_pdf/',views.upload_pdf),
    path('printout/',views.services),
    path('admin_login/',views.admin_login),
    path('admin_home/',views.admin_home),
    path('order/',views.orders)
]
