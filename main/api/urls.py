from django.contrib import admin
from django.urls import path
from .views import CompanyView, RoleView, EmployeeView, ShiftView, UserView

urlpatterns = [
    path('role/', RoleView.as_view(), name='role'),

    path('user/', UserView.as_view(), name='user'),
    path('user/<int:pk>', UserView.as_view(), name='user-details'),

    path('company/', CompanyView.as_view(), name='company'),
    path('company/<int:pk>', CompanyView.as_view(), name='company-details'),

    path('employee/', EmployeeView.as_view(), name='employee'),
    path('employee/<int:emp_id>', EmployeeView.as_view(), name='employee-details'),

    path('shift/', ShiftView.as_view(), name='shift'),
    path('shift/<int:pk>', ShiftView.as_view(), name='shift-details'),
]