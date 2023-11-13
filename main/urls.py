from django.urls import path
from .views import (LoginUser, ProfileView, ShiftView, CompanyView, AcceptCompView,
                    CompanyCreateView, CompanyEditView, CompanyDetailsView, LogoutUser, EditProfile,
                    CompanyEmpAddView, CompanyShiftAddView, AllEmployeesView, EmployeeDetailsView)

urlpatterns = [
    path('', ProfileView.as_view()),
    path('profile', ProfileView.as_view(), name='profile'),
    path('profile/edit', EditProfile.as_view(), name='profile-edit'),
    path('logout', LogoutUser.as_view(), name='logout'),

    path('shift/', ShiftView.as_view(), name='my-shift'),

    path('company/', CompanyView.as_view(), name='company-list'),
    path('company/add', CompanyCreateView.as_view(), name='company-create'),
    path('company/<int:pk>/', CompanyDetailsView.as_view(), name='manage-company'),
    path('company/<int:pk>/edit', CompanyEditView.as_view(), name='company-edit'),
    path('company/<int:pk>/delete', CompanyDetailsView.as_view(), name='company-delete'),
    path('company/<int:pk>/accept', AcceptCompView.as_view(), name='company-accept'),

    path('company/<int:pk>/add_employee', CompanyEmpAddView.as_view(), name='add-employee'),
    path('company/<int:pk>/add_shift', CompanyShiftAddView.as_view(), name='add-shift'),

    path('employee/all', AllEmployeesView.as_view(), name='all-employees'),
    path('employee/<int:pk>/', EmployeeDetailsView.as_view(), name='manage-employee'),
    path('employee/<int:pk>/remove', EmployeeDetailsView.as_view(), name='remove-employee'),
]