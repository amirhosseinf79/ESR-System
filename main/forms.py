from django import forms
from .models import Company, Employee, User, Profile, Role
from django.db.utils import IntegrityError
import re


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        exclude = ('is_deleted', 'created_by')
        widgets = {
            'foundation_date': forms.DateInput(attrs={'type': 'date'})
        }


class EmployeeForm(forms.ModelForm):
    GENDER_CHOICES = []
    roles = Role.objects.all()

    for role in roles:
        GENDER_CHOICES.append((role.id, role.name))

    username = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    role = forms.ChoiceField(choices=GENDER_CHOICES)
    phone_number = forms.CharField(max_length=13, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ('username', 'role', 'password', 'first_name', 'last_name', 'phone_number', 'email')

    def __init__(self, request, company_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_id = company_id
        self.request = request
        self.user_exists = None
        self.get_role = None

    def clean(self):
        profile_check = Profile.objects.filter(phone_number=self.cleaned_data['phone_number'])
        user_check = User.objects.filter(username=self.cleaned_data['username'])
        email_check = User.objects.filter(email=self.cleaned_data['email'])
        employee_check = Employee.objects.filter(user__username=self.cleaned_data['username'],
                                                 company_id=self.company_id)

        company_check = Company.objects.filter(id=self.company_id, created_by=self.request.user)

        if self.request.user.username == self.cleaned_data['username']:
            raise forms.ValidationError({'username': 'You can not add yourself as Employee!'})

        try:
            self.get_role = Role.objects.get(id=self.cleaned_data['role'])
        except Role.DoesNotExist:
            raise forms.ValidationError({'role': 'Role does not exists!'})

        if employee_check.count():
            raise forms.ValidationError({'username': 'Employee is already joined to this company!'})

        if not company_check.count():
            raise forms.ValidationError('Company id is invalid!')

        if user_check.count():
            self.user_exists = user_check.first()
        else:
            for key in self.fields.keys():
                if not self.cleaned_data[key]:
                    real_name = re.sub('_', ' ', key).capitalize()
                    raise forms.ValidationError({key: f'{real_name} can not be empty.'})

            if profile_check.count():
                raise forms.ValidationError({'phone_number': 'Phone number is already in use!'})

            if email_check.count():
                raise forms.ValidationError({'email': 'Email is already in use!'})

        return self.cleaned_data

    def save(self, commit=True):
        if not self.user_exists:
            obj = super().save(commit=commit)
            obj.set_password(self.cleaned_data['password'])
            obj.profile.phone_number = self.cleaned_data['phone_number']
            obj.profile.save()
            obj.save()
        else:
            obj = self.user_exists
        try:
            obj = Employee.objects.create(user=obj,
                                          company_id=self.company_id,
                                          role=self.get_role)
        except IntegrityError:
            obj = Employee.objects_all.get(user=obj, company_id=self.company_id)
            obj.is_deleted = False
            obj.save()

        return obj


class UserForm(forms.ModelForm):
    username = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    phone_number = forms.CharField(max_length=13, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ('username', 'password', 'first_name', 'last_name', 'phone_number', 'email')

    def clean(self):
        super().clean()
        profile_check = Profile.objects.filter(phone_number=self.cleaned_data['phone_number'])
        email_check = User.objects.filter(email=self.cleaned_data['email'])

        for key in self.fields.keys():
            if not self.cleaned_data[key]:
                real_name = re.sub('_', ' ', key).capitalize()
                raise forms.ValidationError({key: f'{real_name} can not be empty.'})

        if profile_check.count():
            raise_err = True
            if self.instance:
                raise_err = False
                if profile_check.first().phone_number != self.instance.profile.phone_number:
                    raise_err = True

            if raise_err:
                raise forms.ValidationError({'phone_number': 'Phone number is already in use!'})

        if email_check.count():
            raise_err2 = True
            if self.instance:
                raise_err2 = False
                if email_check.first().email != self.instance.email:
                    raise_err2 = True

            if raise_err2:
                raise forms.ValidationError({'email': 'Email is already in use!'})

        return self.cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=commit)
        obj.set_password(self.cleaned_data['password'])
        obj.profile.phone_number = self.cleaned_data['phone_number']
        obj.profile.save()
        obj.save()
        return obj
