from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import UserSerializer, UserProfileSerializer, UserRegistrationSerializer
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import serializers

# Create your views here.

@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'login', 'csrf_token', 'register']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action in ['create', 'register']:
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            # Log the user in after registration
            login(request, user)
            # Return the user profile data
            profile_serializer = UserProfileSerializer(user.userprofile)
            return Response(profile_serializer.data, status=status.HTTP_201_CREATED)
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
        
        user = authenticate(username=username, password=password)
        if user:
            if not user.is_active:
                return Response(
                    {'error': 'This account is inactive'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            login(request, user)
            serializer = UserProfileSerializer(user.userprofile)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        if request.user.is_authenticated:
            logout(request)
            return Response({'detail': 'Successfully logged out'})
        return Response({'detail': 'Not logged in'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def csrf_token(self, request):
        """
        This endpoint is used to get a CSRF token.
        The @ensure_csrf_cookie decorator will set the CSRF cookie.
        """
        return Response({'detail': 'CSRF cookie set'})
    
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
