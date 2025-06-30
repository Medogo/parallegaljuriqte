# authentication/views.py
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import login
from django.contrib.auth.signals import user_logged_in

from .models import CustomUser
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    LoginSerializer,
    PasswordChangeSerializer
)

class UserRegistrationView(generics.CreateAPIView):
    """Vue pour l'enregistrement des utilisateurs"""
    
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Génération des tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Signal de connexion
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        
        return Response({
            'message': 'Inscription réussie',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access': str(access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Vue pour la connexion des utilisateurs"""
    
    serializer = LoginSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Génération des tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Signal de connexion
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        
        return Response({
            'message': 'Connexion réussie',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access': str(access_token),
                'refresh': str(refresh),
            }
        })
    
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

class UserProfileView(generics.RetrieveAPIView):
    """Vue pour récupérer le profil utilisateur"""
    
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class UserProfileUpdateView(generics.UpdateAPIView):
    """Vue pour mettre à jour le profil utilisateur"""
    
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        updated_user = serializer.save()
        
        return Response({
            'message': 'Profil mis à jour avec succès',
            'user': UserProfileSerializer(updated_user).data
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """Vue pour changer le mot de passe"""
    
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        
        return Response({
            'message': 'Mot de passe modifié avec succès'
        })
    
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Vue pour la déconnexion (blacklist du refresh token)"""
    
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Déconnexion réussie'
        })
    except Exception as e:
        return Response({
            'error': 'Token invalide'
        }, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenRefreshView(TokenRefreshView):
    """Vue personnalisée pour le rafraîchissement des tokens"""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            response.data['message'] = 'Token rafraîchi avec succès'
        
        return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats_view(request):
    """Vue pour obtenir les statistiques utilisateur"""
    
    user = request.user
    
    # Ces statistiques seront complétées après l'implémentation des modules
    stats = {
        'user_info': {
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'commune': user.commune,
            'preferred_language': user.get_preferred_language_display(),
            'registration_date': user.registration_date,
            'age': user.age,
        },
        'progress': {
            'modules_completed': 0,  # À implémenter
            'total_modules': 10,
            'completion_percentage': 0,  # À implémenter
            'certificates_earned': 0,  # À implémenter
        },
        'activity': {
            'last_login': None,  # À implémenter
            'total_time_spent': 0,  # À implémenter
            'quiz_attempts': 0,  # À implémenter
        }
    }
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check_view(request):
    """Vue pour vérifier l'état de l'API"""
    
    return Response({
        'status': 'healthy',
        'message': 'Paralegal API is running',
        'version': '1.0.0'
    })