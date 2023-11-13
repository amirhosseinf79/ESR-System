from rest_framework import serializers
from ..models import Company, Role, Employee, Shift, User, Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('phone_number', )


class ShowUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'profile')


class EditUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=13)

    class Meta:
        fields = ('id', 'username', 'email', 'password', 'phone_number')
        extra_kwargs = {
            'password': {'write_only': True},
            'phone_number': {'write_only': True}
        }

    def validate_data(self, validated_data, instance=None):
        mail = validated_data['email']
        username = validated_data['username']
        number = validated_data['phone_number']
        email_obj = User.objects.filter(email=mail)
        user_name_obj = User.objects.filter(username=username)
        number_obj = User.objects.filter(profile__phone_number=number)

        error_data = {}

        check_mail = instance.email != mail if instance else True
        check_username = instance.username != username if instance else True
        try:
            check_number = instance.profile.phone_number != number if instance else True
        except Exception as e:
            check_number = True

        if email_obj.count() and check_mail:
            error_data.update({'email': 'Email already exists.'})

        if user_name_obj.count() and check_username:
            error_data.update({'username': 'Username already exists.'})

        if number_obj.count() and check_number:
            error_data.update({'phone_number': 'Phone number already exists.'})

        return error_data

    def create(self, validated_data):
        mail = validated_data['email']
        username = validated_data['username']
        number = validated_data['phone_number']

        error_data = self.validate_data(self.validated_data)
        if error_data:
            raise serializers.ValidationError(error_data)

        instant = User.objects.create(username=username, email=mail)
        instant.set_password(self.validated_data['password'])
        instant.save()
        instant.profile.phone_number = number
        instant.profile.save()
        return instant

    def update(self, instance, validated_data):
        error_data = self.validate_data(self.validated_data, instance)
        if error_data:
            raise serializers.ValidationError(error_data)

        try:
            user_obj = User.objects.get(id=instance.id)
        except User.DoesNotExist:
            raise serializers.ValidationError({'User': 'User does not exist'})
        else:
            user_obj.username = validated_data.get('username', instance.username)
            user_obj.email = validated_data.get('email', instance.email)

            try:
                user_obj.profile.phone_number = validated_data.get('phone_number', instance.profile.phone_number)
                user_obj.profile.save()
            except Exception as e:
                obj = Profile.objects.create(
                    user=user_obj,
                    phone_number=validated_data.get('phone_number', None)
                )
                obj.save()

            password = validated_data.get('password', None)
            if password:
                user_obj.set_password(password)

            user_obj.save()
            return user_obj


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        exclude = ('is_deleted', )


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        exclude = ('is_deleted', )


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        exclude = ('is_deleted', )


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        exclude = ('is_deleted',)
