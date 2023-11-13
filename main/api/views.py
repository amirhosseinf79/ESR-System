from rest_framework.views import APIView
from django.http import Http404
from ..models import Company, Role, Employee, Shift, User
from .serializers import (CompanySerializer, RoleSerializer, EmployeeSerializer,
                          ShiftSerializer, EditUserSerializer, ShowUserSerializer)
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect
from django.db.models import Q

from ..helper.exceptions import CustomError, ForbiddenException


class DefaultView(APIView):
    serializer_class = None
    object_class = None
    redirect_url = None

    def get_query(self, request, fetch="or", **query):
        set_query = Q()
        for k, v in query.items():
            if fetch == 'or':
                set_query |= Q(**{k: v})
            else:
                set_query &= Q(**{k: v})
        return set_query

    def get_object(self, request, pk=None):
        query = self.get_query(request)

        search_query = Q()
        for key in request.GET.keys():
            if key != 'format':
                search_query = search_query & Q(**{f"{key}__contains": request.GET[key]})

        query &= search_query if search_query != Q() else query
        try:
            if pk:
                obj = self.object_class.objects.get(Q(id=pk) & query)
            else:
                obj = self.object_class.objects.filter(query)

        except self.object_class.DoesNotExist:
            raise Http404

        except Exception as e:
            print(e)
            raise Http404

        if not obj:
            raise Http404

        return obj, True if not pk else False

    def access_denied(self):
        return Response({'details': 'Accesss Denied.'}, status=status.HTTP_403_FORBIDDEN)

    def get(self, request, pk=None):
        _obj, many = self.get_object(request, pk)
        serializer = self.serializer_class(_obj, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            obj = serializer.save()
            return redirect(self.redirect_url, pk=obj.id)

        return Response(serializer.errors, status=status.HTTP_201_CREATED)

    def put(self, request, pk=None):
        if not pk:
            raise Http404

        _obj, many = self.get_object(request, pk)
        serializer = self.serializer_class(_obj, data=request.data)

        if serializer.is_valid():
            obj = serializer.save()
            return redirect(self.redirect_url, pk=obj.id)

        return Response(serializer.errors, status=status.HTTP_201_CREATED)

    def delete(self, request, pk=None):
        if not pk:
            raise Http404

        _obj, many = self.get_object(request, pk)
        _obj.is_deleted = True
        _obj.save()
        return Response({'details': 'Object Deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


class UserView(DefaultView):
    serializer_class = EditUserSerializer
    object_class = User
    redirect_url = "user-details"

    def get_query(self, request, fetch="or", **query):
        return super().get_query(request, **{"username": request.GET.get('username', None)})

    def get(self, request, pk=None):
        self.serializer_class = ShowUserSerializer
        return super().get(request, pk)

    def put(self, request, pk=None):
        uid = request.user.id if request.user else None
        return super().put(request, pk=uid)


class CompanyView(DefaultView):
    serializer_class = CompanySerializer
    object_class = Company
    redirect_url = "company-details"

    def get_query(self, request, fetch="or", **query):
        return super().get_query(request, **{"employees__user": request.user, "created_by": request.user})

    def post(self, request):
        request.data['created_by'] = request.user.id
        return super().post(request)


class RoleView(DefaultView):
    serializer_class = RoleSerializer
    object_class = Role
    redirect_url = "role-details"


class EmployeeView(DefaultView):
    serializer_class = EmployeeSerializer
    object_class = Employee
    redirect_url = "employee-details"

    def get_query(self, request, fetch="or", **query):
        return super().get_query(request, **{"user": request.user, "company__created_by": request.user})

    def post(self, request):
        try:
            comp_obj = Company.objects.get(created_by=request.user)
        except Company.DoesNotExist:
            return self.access_denied()
        else:
            request.data['company'] = comp_obj.id
            return super().post(request)


class ShiftView(DefaultView):
    serializer_class = ShiftSerializer
    object_class = Shift
    redirect_url = "shift-details"

    def get_query(self, request, fetch="or", **query):
        qq = {"employee__user": request.user, "employee__company__created_by": request.user}
        return super().get_query(request, **qq)

    def post(self, request):
        try:
            obj = Shift()
            company_id = request.GET.get('company_id', None)
            result = obj.add_shift(request.user, company_id)
        except ForbiddenException:
            return self.access_denied()
        except CustomError as e:
            result = e

        return Response({'details': result})

    def put(self, request, pk=None):
        return self.access_denied()
