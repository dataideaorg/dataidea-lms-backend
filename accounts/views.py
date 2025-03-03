from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import UserSerializer, UserProfileSerializer, UserRegistrationSerializer
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import serializers
from .services import AuthService
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.

@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'login', 'register']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action in ['create', 'register']:
            return UserRegistrationSerializer
        return UserSerializer
    
    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            
            # First, try to register with the main backend
            main_backend_response = AuthService.register_with_main_backend(serializer.validated_data)
            
            # If main backend registration is successful, create local user
            try:
                user = User.objects.get(username=serializer.validated_data['username'])
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=serializer.validated_data['username'],
                    password=serializer.validated_data['password'],
                    first_name=serializer.validated_data['first_name'],
                    last_name=serializer.validated_data['last_name'],
                    email=serializer.validated_data.get('email', '')
                )
                # Create associated profile
                UserProfile.objects.get_or_create(user=user)
            
            # Generate tokens
            tokens = self.get_tokens_for_user(user)
            
            # Return the user profile data and tokens
            profile_serializer = UserProfileSerializer(user.userprofile)
            return Response({
                **profile_serializer.data,
                **tokens
            }, status=status.HTTP_201_CREATED)
            
        except serializers.ValidationError as e:
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Both username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # First, try to authenticate with the main backend
        auth_response = AuthService.authenticate_with_main_backend(username, password)
        if not auth_response:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If main backend authentication successful, get or create local user
        try:
            user = User.objects.get(username=username)
            # Update user info if needed
            user.save()
        except User.DoesNotExist:
            # Create new user in LMS database
            user = User.objects.create_user(
                username=username,
                password=password  # This will be hashed by Django
            )
            # Create associated profile
            UserProfile.objects.get_or_create(user=user)
        
        # Generate tokens
        tokens = self.get_tokens_for_user(user)
        
        # Return user profile data and tokens
        serializer = UserProfileSerializer(user.userprofile)
        return Response({
            **serializer.data,
            **tokens
        })
    
    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if request.method == 'GET':
            serializer = UserProfileSerializer(request.user.userprofile)
            return Response(serializer.data)
        
        elif request.method == 'PATCH':
            user = request.user
            profile = user.userprofile
            
            # Update user fields
            if 'first_name' in request.data:
                user.first_name = request.data['first_name']
            if 'last_name' in request.data:
                user.last_name = request.data['last_name']
            if 'email' in request.data:
                # Check if email is already taken
                if User.objects.exclude(pk=user.pk).filter(email=request.data['email']).exists():
                    return Response(
                        {'error': 'This email is already in use'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                user.email = request.data['email']
            user.save()
            
            # Update profile fields
            if 'bio' in request.data:
                profile.bio = request.data['bio']
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_type = self.request.query_params.get('user_type', None)
        queryset = UserProfile.objects.all()
        
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        return queryset
