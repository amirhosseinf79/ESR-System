from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.utils import timezone

from .helper.ModelManager import DeletedManager, EmployeeManager
from .helper.exceptions import ForbiddenException, CustomError
from .helper.utils import generate_rand_string


def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user_id=instance.id)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=13, null=True, blank=True)

    def __str__(self):
        return self.user.username


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    number = models.IntegerField(unique=True, verbose_name='Company Number')
    city = models.CharField(max_length=55)
    create_date = models.DateTimeField(auto_now_add=True)
    foundation_date = models.DateField()
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="companies")

    objects_all = models.Manager()
    objects = DeletedManager()

    class Meta:
        unique_together = ('name', 'number')
        verbose_name_plural = 'companies'
        ordering = ('-foundation_date', '-create_date', )

    def clean(self):
        if self.foundation_date > timezone.now().date():
            raise ValidationError(f"Company Foundation date must be lowr than {timezone.now().date()}")
        if self.id:
            try:
                obj = Company.objects.get(id=self.id)
            except Company.DoesNotExist:
                pass
            else:
                if obj.created_by != self.created_by and not obj.created_by.is_staff:
                    raise ValidationError(f"You don't have permission to change {self.__class__.__name__} information.")

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=55)
    is_deleted = models.BooleanField(default=False)

    objects_all = models.Manager()
    objects = DeletedManager()

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Employee(models.Model):
    uid = models.CharField(max_length=20, default=generate_rand_string(), unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employee_info')
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='employees')
    role = models.ForeignKey('Role', on_delete=models.CASCADE, related_name='employee_role')
    is_deleted = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)

    objects_all = models.Manager()
    objects = EmployeeManager()

    class Meta:
        unique_together = ('user', 'company')
        ordering = ('company', 'user')

    def clean(self):
        if self.id:
            try:
                obj = Employee.objects.get(id=self.id)
            except Employee.DoesNotExist:
                pass
            else:
                if not obj.user.is_staff:
                    if obj.user != self.user or obj.company != self.company:
                        raise ValidationError(f"You can't change {self.__class__.__name__} information.")

    def __str__(self):
        return self.user.username


class Shift(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='employee')
    enter_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    objects_all = models.Manager()
    objects = DeletedManager()

    class Meta:
        ordering = ('-enter_time', '-exit_time')

    def clean(self):
        if self.id and not self.is_deleted and not self.employee.user.is_staff and self.exit_time:
            raise ValidationError("Shift time is not editable.")

        if self.enter_time and not self.exit_time:
            self.exit_time = timezone.now()
        else:
            self.enter_time = timezone.now()

        if self.exit_time:
            if self.exit_time < self.enter_time:
                raise ValidationError(f"Shift Time is not valid.")

    def add_shift_sys(self, emp_obj):
        try:
            obj = Shift.objects.get(exit_time=None, employee=emp_obj)
        except Shift.DoesNotExist:
            self.employee = emp_obj
            self.clean()
            self.save()

            if not self.exit_time:
                result = f"Shift Started on {self.enter_time.strftime('%Y/%m/%d at %H:%M')}."
            else:
                result = f"Shift Ended on {self.exit_time.strftime('%Y/%m/%d at %H:%M')}."
        else:
            obj.clean()
            obj.save()

            if obj.exit_time:
                result = f"Shift Ended on {obj.exit_time.strftime('%Y/%m/%d at %H:%M')}."
            else:
                raise CustomError(f"Something went wrong")

        return result

    def add_shift_by_uid(self, uid):
        try:
            emp_obj = Employee.objects.get(uid=uid)
        except Employee.DoesNotExist:
            raise ForbiddenException()

        return self.add_shift_sys(emp_obj)

    def add_shift(self, user, company_id=None):
        try:
            emp_obj = Employee.objects.get(user=user, company_id=company_id)
        except Employee.DoesNotExist:
            raise ForbiddenException()

        return self.add_shift_sys(emp_obj)

    def __str__(self):
        return f"{self.id}"

    post_save.connect(create_profile, sender=User)
