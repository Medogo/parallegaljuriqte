# authentication/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import CustomUser
from datetime import date

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'enregistrement des utilisateurs"""
    
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'full_name', 'phone_number', 'commune', 'gender',
            'birth_date', 'education_level', 'preferred_language',
            'password', 'password_confirm'
        ]
    
    def validate_birth_date(self, value):
        """Valide que l'utilisateur a au moins 16 ans"""
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if age < 16:
            raise serializers.ValidationError(
                "L'utilisateur doit avoir au moins 16 ans pour s'inscrire."
            )
        if age > 100:
            raise serializers.ValidationError(
                "Veuillez vérifier la date de naissance saisie."
            )
        return value
    
    def validate_phone_number(self, value):
        """Valide le format du numéro de téléphone"""
        # Nettoyage du numéro
        cleaned_number = ''.join(filter(str.isdigit, value))
        
        # Vérification pour les numéros béninois
        if len(cleaned_number) == 8 and cleaned_number.startswith(('9', '6', '4')):
            return f"+229{cleaned_number}"
        elif len(cleaned_number) == 11 and cleaned_number.startswith('229'):
            return f"+{cleaned_number}"
        elif value.startswith('+229') and len(value) == 12:
            return value
        else:
            raise serializers.ValidationError(
                "Format de numéro invalide. Utilisez le format béninois: +229XXXXXXXX"
            )
    
    def validate(self, attrs):
        """Validation croisée des champs"""
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Les mots de passe ne correspondent pas.'
            })
        
        # Validation du mot de passe Django
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})
        
        return attrs
    
    def create(self, validated_data):
        """Crée un nouvel utilisateur"""
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""
    
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'full_name', 'phone_number', 'commune', 'gender',
            'birth_date', 'age', 'education_level', 'preferred_language',
            'registration_date', 'is_profile_complete'
        ]
        read_only_fields = ['id', 'phone_number', 'registration_date', 'is_profile_complete']

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour du profil"""
    
    class Meta:
        model = CustomUser
        fields = [
            'full_name', 'commune', 'gender', 'birth_date', 
            'education_level', 'preferred_language'
        ]
    
    def validate_birth_date(self, value):
        """Valide que l'utilisateur a au moins 16 ans"""
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if age < 16:
            raise serializers.ValidationError(
                "L'utilisateur doit avoir au moins 16 ans."
            )
        if age > 100:
            raise serializers.ValidationError(
                "Veuillez vérifier la date de naissance saisie."
            )
        return value

class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion"""
    
    phone_number = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')
        
        if phone_number and password:
            # Nettoyage et formatage du numéro
            cleaned_number = ''.join(filter(str.isdigit, phone_number))
            if len(cleaned_number) == 8:
                phone_number = f"+229{cleaned_number}"
            elif not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"
            
            user = authenticate(
                request=self.context.get('request'),
                username=phone_number,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Numéro de téléphone ou mot de passe incorrect.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'Ce compte a été désactivé.'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Le numéro de téléphone et le mot de passe sont requis.'
            )

class PasswordChangeSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe"""
    
    old_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        min_length=8
    )
    new_password_confirm = serializers.CharField(style={'input_type': 'password'})
    
    def validate_old_password(self, value):
        """Vérifie l'ancien mot de passe"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Ancien mot de passe incorrect.')
        return value
    
    def validate(self, attrs):
        """Validation croisée des nouveaux mots de passe"""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': 'Les nouveaux mots de passe ne correspondent pas.'
            })
        
        # Validation du mot de passe Django
        try:
            validate_password(new_password, user=self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
        
        return attrs
    
    def save(self):
        """Sauvegarde le nouveau mot de passe"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user