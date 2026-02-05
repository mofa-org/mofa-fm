"""
用户视图
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from utils.math_captcha import generate_math_question
from .models import User, CreatorVerification
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    CreatorVerificationSerializer,
    VerifyAnswerSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """用户注册"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # 生成 JWT token
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """用户登录"""
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': '请提供用户名和密码'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 支持邮箱登录
    if '@' in username:
        try:
            user = User.objects.get(email=username)
            username = user.username
        except User.DoesNotExist:
            pass

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': '用户名或密码错误'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # 生成 JWT token
    refresh = RefreshToken.for_user(user)

    return Response({
        'user': UserSerializer(user).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """获取当前用户信息"""
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """更新用户资料"""
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 创作者验证相关视图

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def become_creator(request):
    """申请成为创作者 - 直接通过"""
    user = request.user

    if user.is_creator:
        return Response({'error': '您已经是创作者了'}, status=status.HTTP_400_BAD_REQUEST)

    # 直接设置为创作者
    user.is_creator = True
    user.save()

    return Response({
        'success': True,
        'message': '恭喜！您已成为创作者',
        'user': UserSerializer(user).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_creator(request):
    """验证数学题答案"""
    user = request.user

    if user.is_creator:
        return Response({'error': '您已经是创作者了'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        verification = CreatorVerification.objects.get(user=user)
    except CreatorVerification.DoesNotExist:
        return Response(
            {'error': '请先申请成为创作者'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 尝试次数无限制

    serializer = VerifyAnswerSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    answer = serializer.validated_data['answer']

    # 验证答案
    if verification.verify(answer):
        return Response({
            'success': True,
            'message': '恭喜！您已成为创作者',
            'user': UserSerializer(user).data
        })
    else:
        attempts_left = 3 - verification.attempts
        return Response({
            'success': False,
            'message': '答案错误，请重试',
            'attempts_left': attempts_left
        }, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(generics.RetrieveAPIView):
    """用户详情"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    lookup_field = 'username'
