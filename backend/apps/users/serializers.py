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
            'is_creator', 'is_verified', 'shows_count', 'total_plays',
            'created_at'
        ]
        read_only_fields = ['id', 'is_creator', 'is_verified', 'shows_count', 'total_plays', 'created_at']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


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
