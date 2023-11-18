from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotFound
from .helper.exceptions import CustomError, ForbiddenException
from django.views import View
from django.urls import reverse

from .models import Shift, Company, Employee
from .forms import CompanyForm, EmployeeForm, UserForm
import qrcode
import re


def process_current_site_url(request):
    curl = re.sub('http.?://', '', request.build_absolute_uri())
    curl = re.sub('\?(.+)', '', curl)
    curl_splited = re.split("/", curl)
    curl_splited = curl_splited[1:]

    result = []

    for i, item in enumerate(curl_splited):
        if item:
            data = {
                'name': '>'.join(curl_splited[:i+1]),
                'url': '/' + '/'.join(curl_splited[:i+1]) + '/'
            }
            result.append(data)

    return result


def generate_qr(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f'main/static/img/emp/{data}.png')


# Create your views here.
class LoginUser(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True
    extra_context = {'title': 'Login'}
    next_page = 'profile'


class RegisterView(View):
    def get(self, request):
        form = UserForm()
        data = {
            'title': 'Create Account',
            'url_three': process_current_site_url(request),
            'form': form
        }
        return render(request, 'registration/login.html', data)

    def post(self, request):
        form = UserForm(request.POST)

        data = {
            'title': 'Edit User Profile',
            'url_three': process_current_site_url(request),
            'form': form
        }

        if form.is_valid():
            form.save()
            return redirect('profile')

        return render(request, 'panel/profile/edit.html', data)


class LogoutUser(LogoutView):
    next_page = 'login'


class ProfileView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        data = {
            'title': 'User Information',
            'url_three': process_current_site_url(request)
        }

        paginated_obj, obj = Shift.objects.get_paginated(request, employee__user=request.user)
        data['shift_list'] = paginated_obj

        return render(request, 'panel/profile/show.html', data)


class EditProfile(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        form = UserForm(instance=request.user)
        data = {
            'title': 'Edit User Profile',
            'url_three': process_current_site_url(request),
            'form': form
        }
        return render(request, 'panel/profile/edit.html', data)

    def post(self, request):
        form = UserForm(request.POST, instance=request.user)

        data = {
            'title': 'Edit User Profile',
            'url_three': process_current_site_url(request),
            'form': form
        }

        if form.is_valid():
            form.save()
            return redirect('profile')

        return render(request, 'panel/profile/edit.html', data)


class ShiftView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        data = {
            'title': 'My Shift Records',
            'url_three': process_current_site_url(request)
        }
        paginated_obj, obj = Shift.objects.get_paginated(request, employee__user=request.user)
        data['shift_list'] = paginated_obj

        return render(request, 'panel/shift.html', data)


class CompanyView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        data = {
            'title': 'My Companies',
            'url_three': process_current_site_url(request)
        }

        companies_owned, companies_owned_obj = Company.objects.get_paginated(request, created_by=request.user)
        companies_emp, companies_emp_obj = Company.objects.get_paginated(request,
                                                                           employees__user=request.user,
                                                                           employees__is_deleted=False,
                                                                           employees__is_accepted=True)

        pending_companies, pending_companies_obj = Company.objects.get_paginated(request,
                                                                                 employees__user=request.user,
                                                                                 employees__is_deleted=False,
                                                                                 employees__is_accepted=False)
        data['companies_owned'] = companies_owned
        data['companies_employee'] = companies_emp
        data['pending_companies'] = pending_companies

        data['companies_owned_c'] = companies_owned_obj.count()
        data['companies_employee_c'] = companies_emp_obj.count()
        data['pending_companies_c'] = pending_companies_obj.count()

        return render(request, 'panel/company/list.html', data)


class CompanyCreateView(LoginRequiredMixin, View):
    login_url = 'login'
    form_class = CompanyForm

    def get(self, request):
        data = {
            'title': 'Add New Company',
            'form': self.form_class(),
            'url_three': process_current_site_url(request)
        }
        return render(request, 'panel/company/create.html', data)

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            return redirect('company-list')

        data = {
            'title': 'Add New Company',
            'form': form,
            'url_three': process_current_site_url(request)
        }
        return render(request, 'panel/company/create.html', data)


class CompanyDetailsView(LoginRequiredMixin, View):
    login_url = 'login'

    def get_obj(self, request, pk):
        emp_list = []
        shift_list = []
        creator = False
        emp_obj = 0
        try:
            obj = Company.objects.get(id=pk, created_by=request.user)
        except Company.DoesNotExist:
            try:
                obj = Company.objects.get(id=pk,
                                          employees__user=request.user,
                                          employees__is_deleted=False,
                                          employees__is_accepted=True)
            except Company.DoesNotExist:
                obj = None

        if obj:
            if obj.created_by == request.user:
                emp_list, emp_obj = Employee.objects.get_paginated(request, company=obj)
                creator = True

            if creator:
                shift_list, _obj = Shift.objects.get_paginated(request, employee__company=obj)
            else:
                shift_list, _obj = Shift.objects.get_paginated(request,
                                                               employee__user=request.user, employee__company=obj)

        data = {
            'object': obj,
            'employees': emp_list,
            'employees_c': emp_obj if emp_obj == 0 else emp_obj.count(),
            'shift_list': shift_list,
            'is_creator': creator
        }
        return data

    def get(self, request, pk):
        data = self.get_obj(request, pk)
        if not data['object']:
            return HttpResponseNotFound()

        data.update({'title': f"{data['object'].name} Details"})
        data.update({'result': request.GET.get('result', '')})
        data.update({'url_three': process_current_site_url(request)})
        return render(request, 'panel/company/details.html', data)

    def post(self, request, pk):
        try:
            obj = Company.objects.get(id=pk, created_by=request.user)
        except Company.DoesNotExist:
            return HttpResponseNotFound()
        else:
            obj.is_deleted = True
            obj.save()
            return redirect('company-list')


class CompanyEditView(CompanyDetailsView):
    login_url = 'login'
    form_class = CompanyForm

    def get_obj(self, request, pk):
        data = super().get_obj(request, pk)
        if data['is_creator']:
            return data['object']

        return None

    def get(self, request, pk):
        instance = self.get_obj(request, pk)
        if not instance:
            return redirect('manage-company', pk=pk)

        data = {
            'title': f"Edit Company: {instance.name}",
            'form': self.form_class(instance=instance),
            'url_three': process_current_site_url(request)
        }
        return render(request, 'panel/company/create.html', data)

    def post(self, request, pk):
        instance = self.get_obj(request, pk)
        if not instance:
            return redirect('manage-company', pk=pk)

        form = self.form_class(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            return redirect('manage-company', pk=pk)

        data = {
            'title': f"Edit Company: {instance.name}",
            'url_three': process_current_site_url(request),
            'form': form
        }
        return render(request, 'panel/company/create.html', data)


class CompanyEmpAddView(CompanyDetailsView):
    login_url = 'login'
    form_class = EmployeeForm

    def get(self, request, pk):
        check_data = self.get_obj(request, pk)
        if not check_data['is_creator']:
            return redirect('manage-company', pk=pk)

        data = {
            'title': f"Add Employee",
            'form': EmployeeForm(request, pk),
            'url_three': process_current_site_url(request)
        }
        return render(request, 'panel/company/add_employee.html', data)

    def post(self, request, pk):
        check_data = self.get_obj(request, pk)
        if not check_data['is_creator']:
            return redirect('manage-company', pk=pk)

        data = {
            'title': f"Add Employee",
            'url_three': process_current_site_url(request)
        }
        form = EmployeeForm(request, pk, request.POST)
        if form.is_valid():
            obj = form.save()
            data['result'] = f"{obj.user.username} ({obj.user.first_name} {obj.user.last_name}) added successfully!"

        data['form'] = form

        return render(request, 'panel/company/add_employee.html', data)


class CompanyShiftAddView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, pk):
        try:
            obj = Shift()
            result = obj.add_shift(request.user, pk)
        except ForbiddenException as e:
            print(e)
            result = e
        except CustomError as e:
            result = e

        return redirect(reverse('manage-company', kwargs={'pk': pk}) + f"?result={result}")


class AcceptCompView(LoginRequiredMixin, View):
    login_url = 'login'

    def get_obj(self, request, pk):
        try:
            obj = Employee.objects_all.get(company_id=pk, user=request.user, is_deleted=False)
        except Employee.DoesNotExist:
            obj = None

        return obj

    def get(self, request, pk):
        obj = self.get_obj(request, pk)
        if obj:
            if bool(request.GET.get('accept', False)):
                obj.is_accepted = True
            else:
                obj.is_deleted = True
            obj.save()

        return redirect('company-list')


class AllEmployeesView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        data = {
            'title': 'My Employees',
            'url_three': process_current_site_url(request)
        }
        obj_list, obj = Employee.objects.get_paginated(request,
                                                       company__created_by=request.user,
                                                       company__is_deleted=False)
        data['employees'] = obj_list

        return render(request, 'panel/employee/list.html', data)


class EmployeeDetailsView(LoginRequiredMixin, View):
    login_url = 'login'

    def get_obj(self, request, pk):
        shift_list = []

        try:
            obj = Employee.objects.get(id=pk, user=request.user)
        except Employee.DoesNotExist:
            try:
                obj = Employee.objects.get(id=pk, company__created_by=request.user, company__is_deleted=False)
            except Employee.DoesNotExist:
                obj = None

        if obj:
            shift_list, _obj = Shift.objects.get_paginated(request, employee=obj)

        data = {
            'object': obj,
            'shift_list': shift_list,
            'object_qr': f'img/emp/{obj.uid}.png'
        }

        return data

    def get(self, request, pk):
        data = self.get_obj(request, pk)
        if not data['object']:
            return HttpResponseNotFound()

        # generate_qr(data['object'].uid)

        data.update({
            'title': f"Employee Details",
            'url_three': process_current_site_url(request)
        })
        return render(request, 'panel/employee/details.html', data)

    def post(self, request, pk):
        obj = self.get_obj(request, pk)
        if not obj:
            return HttpResponseNotFound()

        obj['object'].is_deleted = True
        obj['object'].save()

        return redirect('all-employees')
