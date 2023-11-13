from django.db import models
from .utils import paginate


class DeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def get_paginated(self, request, **kwargs):
        page = request.GET.get('page', 1)
        obj = self.filter(**kwargs)
        return paginate(page, obj), obj


class EmployeeManager(DeletedManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_accepted=True)
