"""
用户序列化器
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, CreatorVerification


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""

    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'avatar', 'avatar_url', 'bio',
            'is_creator', 'is_verified', 'email_verified', 'shows_count', 'total_plays',
            'created_at'
        ]
        read_only_fields = ['id', 'is_creator', 'is_verified', 'email_verified', 'shows_count', 'total_plays', 'created_at']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        # 返回默认头像
        if request:
            return request.build_absolute_uri('/static/default_avatar.png')
        return '/static/default_avatar.png'


class RegisterSerializer(serializers.ModelSerializer):
    """注册序列化器"""

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "两次密码不一致"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class CreatorVerificationSerializer(serializers.ModelSerializer):
    """创作者验证序列化器"""

    class Meta:
        model = CreatorVerification
        fields = ['question', 'attempts', 'is_verified', 'verified_at']
        read_only_fields = ['question', 'attempts', 'is_verified', 'verified_at']


class VerifyAnswerSerializer(serializers.Serializer):
    """验证答案序列化器"""

    answer = serializers.IntegerField(required=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """请求重置密码序列化器"""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("该邮箱未注册")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """确认重置密码序列化器"""
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    re_new_password = serializers.CharField(write_only=True, required=True)
    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['re_new_password']:
            raise serializers.ValidationError({"new_password": "两次密码不一致"})
        return attrs
