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
    VerifyAnswerSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """请求重置密码"""
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # 生成 token 和 uid
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # 构造链接
        # 前端路由需匹配: /auth/reset-password/:uid/:token
        reset_link = f"{settings.CORS_ALLOWED_ORIGINS[0]}/auth/reset-password/{uid}/{token}"
        
        # 发送邮件
        subject = "MoFA FM - 重置密码"
        message = f"""
        您好 {user.username}，
        
        您收到了这封邮件是因为您请求重置密码。
        请点击下面的链接来重置您的密码：
        
        {reset_link}
        
        如果您没有请求重置密码，请忽略此邮件。
        """
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
            return Response({'message': '重置密码邮件已发送，请检查您的邮箱'})
        except Exception as e:
            return Response({'error': '邮件发送失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """确认重置密码"""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        uidb64 = serializer.validated_data['uidb64']
        token = serializer.validated_data['token']
        password = serializer.validated_data['new_password']
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            
        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(password)
            user.save()
            return Response({'message': '密码重置成功，请使用新密码登录'})
        else:
            return Response({'error': '无效的重置链接或链接已过期'}, status=status.HTTP_400_BAD_REQUEST)
            
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_verification_email(request):
    """发送验证邮件"""
    user = request.user
    if user.email_verified:
        return Response({'message': '您的邮箱已验证'})
        
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    verify_link = f"{settings.CORS_ALLOWED_ORIGINS[0]}/auth/verify-email/{uid}/{token}"
    
    subject = "MoFA FM - 验证您的邮箱"
    message = f"""
    您好 {user.username}，
    
    感谢注册 MoFA FM。请点击下面的链接验证您的邮箱地址：
    
    {verify_link}
    """
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        return Response({'message': '验证邮件已发送'})
    except Exception as e:
        return Response({'error': '邮件发送失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_confirm(request):
    """确认验证邮箱"""
    uidb64 = request.data.get('uidb64')
    token = request.data.get('token')
    
    if not uidb64 or not token:
        return Response({'error': '无效的请求'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'error': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
    if user is not None and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.save()
        return Response({'message': '邮箱验证成功'})
    else:
        return Response({'error': '验证链接无效或已过期'}, status=status.HTTP_400_BAD_REQUEST)


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
    """申请成为创作者 - 生成数学题"""
    user = request.user

    if user.is_creator:
        return Response({'error': '您已经是创作者了'}, status=status.HTTP_400_BAD_REQUEST)

    # 获取或创建验证记录
    verification, created = CreatorVerification.objects.get_or_create(user=user)

    if created or not verification.question:
        # 生成新的数学题
        question, answer = generate_math_question()
        verification.question = question
        verification.answer = answer
        verification.save()

    serializer = CreatorVerificationSerializer(verification)
    return Response(serializer.data)


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

    # 检查尝试次数
    if verification.attempts >= 3:
        return Response(
            {'error': '尝试次数过多，请稍后再试'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

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
