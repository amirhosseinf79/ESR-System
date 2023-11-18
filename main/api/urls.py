from django.contrib import admin
from django.urls import path
from .views import ShiftAddView

urlpatterns = [
    path('shift/add', ShiftAddView.as_view(), name='update-shift'),
]