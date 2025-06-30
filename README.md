# Documentation API Paralegal

## Vue d'ensemble

L'API Paralegal est une interface RESTful construite avec Django REST Framework pour supporter l'application mobile de formation parajuridique. Elle gère l'authentification, les modules de formation, la progression des utilisateurs et les signalements communautaires.

**Base URL :** `https://api.paralegal.example.com/api/`

## Authentification

L'API utilise l'authentification JWT (JSON Web Tokens).

### Inscription
```http
POST /auth/register/
Content-Type: application/json

{
    "full_name": "Jean Dupont",
    "phone_number": "+22912345678",
    "commune": "Cotonou",
    "gender": "M",
    "birth_date": "1990-01-15"
    "education_level": "SECONDARY",
    "preferred_language": "FR",
    "password": "motdepasse123",
    "password_confirm": "motdepasse123"
}
```

**Réponse :**
```json
{
    "message": "Inscription réussie",
    "user": {
        "id": 1,
        "full_name": "Jean Dupont",
        "phone_number": "+22912345678",
        "commune": "Cotonou",
        "preferred_language": "FR"
    },
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
}
```

### Connexion
```http
POST /auth/login/
Content-Type: application/json

{
    "phone_number": "+22912345678",
    "password": "motdepasse123"
}
```

## Modules de formation

### Liste des modules
```http
GET /modules/
Authorization: Bearer <access_token>
```

**Réponse :**
```json
[
    {
        "id": 1,
        "number": 1,
        "title": "Introduction aux parajuristes",
        "description": "Comprendre le rôle et les responsabilités...",
        "is_reporting_module": false,
        "audio_duration": 1200
    }
]
```

### Détail d'un module
```http
GET /modules/{id}/
Authorization: Bearer <access_token>
```

**Réponse (utilisateur français) :**
```json
{
    "id": 1,
    "number": 1,
    "title": "Introduction aux parajuristes",
    "introduction_fr": "Ce module présente...",
    "objectives_fr": "- Comprendre le rôle...",
    "content_fr": "Un parajuriste communautaire...",
    "quiz_questions": [
        {
            "id": 1,
            "order": 1,
            "question_type": "SINGLE",
            "question_text": "Qu'est-ce qu'un parajuriste ?",
            "points": 1,
            "answer_choices": [
                {
                    "id": 1,
                    "choice_text": "Un avocat certifié",
                    "order": 1
                },
                {
                    "id": 2,
                    "choice_text": "Un assistant juridique communautaire",
                    "order": 2
                }
            ]
        }
    ]
}
```

### Soumission de quiz
```http
POST /modules/quiz/submit/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "module_id": 1,
    "started_at": "2024-01-15T10:00:00Z",
    "answers": [
        {
            "question": 1,
            "selected_choices": [2]
        }
    ]
}
```

**Réponse :**
```json
{
    "attempt": {
        "id": 1,
        "module_number": 1,
        "attempt_number": 1,
        "score": 80.0,
        "is_passed": true
    },
    "questions_with_answers": [...],
    "passed": true,
    "message": "Félicitations ! Vous avez réussi le quiz avec 80.0%"
}
```

### Suivi progression audio (Fon)
```http
POST /modules/audio/progress/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "module_id": 1,
    "progress_percentage": 75.0,
    "current_time": 900
}
```

## Progression

### Progression globale
```http
GET /progress/
Authorization: Bearer <access_token>
```

**Réponse :**
```json
{
    "id": 1,
    "user_name": "Jean Dupont",
    "user_language": "FR",
    "total_modules": 9,
    "completed_modules": 3,
    "completion_percentage": 33.3,
    "can_get_certificate": false,
    "next_module": {
        "id": 4,
        "number": 4,
        "title": "Enregistrement des naissances"
    }
}
```

### Demande de certificat
```http
POST /progress/certificate/request/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "full_name": "Jean Dupont"
}
```

**Réponse (utilisateur français) :**
```json
{
    "message": "Certificat généré avec succès",
    "certificate": {
        "id": 1,
        "verification_code": "ABC123XYZ789",
        "full_name": "Jean Dupont",
        "completion_date": "2024-01-15T15:30:00Z",
        "total_modules_completed": 9,
        "average_score": 85.5
    }
}
```

**Réponse (utilisateur Fon) :**
```json
{
    "message": "Félicitations ! Vous avez terminé tous les modules audio...",
    "contact_info": {
        "whatsapp_number": "+229 01 57 57 51 67",
        "organization": "HAI",
        "required_info": [
            "Nom complet",
            "Lieu de résidence", 
            "Capture d'écran de progression 100%"
        ]
    },
    "progress_screenshot_required": true
}
```

### Vérification de certificat
```http
GET /progress/certificate/verify/{verification_code}/
```

**Réponse :**
```json
{
# Documentation API Paralegal

## Vue d'ensemble

L'API Paralegal est une interface RESTful construite avec Django REST Framework pour supporter l'application mobile de formation parajuridique. Elle gère l'authentification, les modules de formation, la progression des utilisateurs et les signalements communautaires.

**Base URL :** `https://api.paralegal.example.com/api/`

## Authentification

L'API utilise l'authentification JWT (JSON Web Tokens).

### Inscription
```http
POST /auth/register/
Content-Type: application/json

{
    "full_name": "Jean Dupont",
    "phone_number": "+22912345678",
    "commune": "Cotonou",
    "gender": "M",
    "birth_date": "1990-01-15",
    "education_level": "SECONDARY",
    "preferred_language": "FR",
    "password": "motdepasse123",
    "password_confirm": "motdepasse123"
}
```

**Réponse :**
```json
{
    "message": "Inscription réussie",
    "user": {
        "id": 1,
        "full_name": "Jean Dupont",
        "phone_number": "+22912345678",
        "commune": "Cotonou",
        "preferred_language": "FR"
    },
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
}
```

### Connexion
```http
POST /auth/login/
Content-Type: application/json

{
    "phone_number": "+22912345678",
    "password": "motdepasse123"
}
```

## Modules de formation

### Liste des modules
```http
GET /modules/
Authorization: Bearer <access_token>
```

**Réponse :**
```json
[
    {
        "id": 1,
        "number": 1,
        "title": "Introduction aux parajuristes",
        "description": "Comprendre le rôle et les responsabilités...",
        "is_reporting_module": false,
        "audio_duration": 1200
    }
]
```

### Détail d'un module
```http
GET /modules/{id}/
Authorization: Bearer <access_token>
```

**Réponse (utilisateur français) :**
```json
{
    "id": 1,
    "number": 1,
    "title": "Introduction aux parajuristes",
    "introduction_fr": "Ce module présente...",
    "objectives_fr": "- Comprendre le rôle...",
    "content_fr": "Un parajuriste communautaire...",
    "quiz_questions": [
        {
            "id": 1,
            "order": 1,
            "question_type": "SINGLE",
            "question_text": "Qu'est-ce qu'un parajuriste ?",
            "points": 1,
            "answer_choices": [
                {
                    "id": 1,
                    "choice_text": "Un avocat certifié",
                    "order": 1
                },
                {
                    "id": 2,
                    "choice_text": "Un assistant juridique communautaire",
                    "order": 2
                }
            ]
        }
    ]
}
```

### Soumission de quiz
```http
POST /modules/quiz/submit/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "module_id": 1,
    "started_at": "2024-01-15T10:00:00Z",
    "answers": [
        {
            "question": 1,
            "selected_choices": [2]
        }
    ]
}
```

**Réponse :**
```json
{
    "attempt": {
        "id": 1,
        "module_number": 1,
        "attempt_number": 1,
        "score": 80.0,
        "is_passed": true
    },
    "questions_with_answers": [...],
    "passed": true,
    "message": "Félicitations ! Vous avez réussi le quiz avec 80.0%"
}
```

### Suivi progression audio (Fon)
```http
POST /modules/audio/progress/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "module_id": 1,
    "progress_percentage": 75.0,
    "current_time": 900
}
```

## Progression

### Progression globale
```http
GET /progress/
Authorization: Bearer <access_token>
```

**Réponse :**
```json
{
    "id": 1,
    "user_name": "Jean Dupont",
    "user_language": "FR",
    "total_modules": 9,
    "completed_modules": 3,
    "completion_percentage": 33.3,
    "can_get_certificate": false,
    "next_module": {
        "id": 4,
        "number": 4,
        "title": "Enregistrement des naissances"
    }
}
```

### Demande de certificat
```http
POST /progress/certificate/request/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "full_name": "Jean Dupont"
}
```

**Réponse (utilisateur français) :**
```json
{
    "message": "Certificat généré avec succès",
    "certificate": {
        "id": 1,
        "verification_code": "ABC123XYZ789",
        "full_name": "Jean Dupont",
        "completion_date": "2024-01-15T15:30:00Z",
        "total_modules_completed": 9,
        "average_score": 85.5
    }
}
```

**Réponse (utilisateur Fon) :**
```json
{
    "message": "Félicitations ! Vous avez terminé tous les modules audio...",
    "contact_info": {
        "whatsapp_number": "+229 01 57 57 51 67",
        "organization": "HAI",
        "required_info": [
            "Nom complet",
            "Lieu de résidence", 
            "Capture d'écran de progression 100%"
        ]
    },
    "progress_screenshot_required": true
}
```

### Vérification de certificat
```http
GET /progress/certificate/verify/{verification_code}/
```

**Réponse :**
```json
{
    "is_valid": true,
    "certificate": {
        "full_name": "Jean Dupont",
        "completion_date": "2024-01-15T15:30:00Z",
        "total_modules_completed": 9,
        "average_score": 85.5,
        "verification_code": "ABC123XYZ789"
    },
    "verified_at": "2024-01-16T10:00:00Z"
}
```

## Signalements

### Informations du module de signalement
```http
GET /reporting/info/
Authorization: Bearer <access_token>
```

**Réponse (utilisateur français) :**
```json
{
    "module_info": {
        "title": "Module de signalement communautaire",
        "description": "Ce module vous permet de signaler...",
        "form_type": "text",
        "action_button": "Créer un signalement"
    },
    "user_stats": {
        "total_reports": 2,
        "pending_reports": 1,
        "resolved_reports": 1
    }
}
```

### Créer un signalement textuel (français)
```http
POST /reporting/text/create/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
    "problem_type": "JUSTICE",
    "title": "Difficulté d'accès au tribunal",
    "description": "Description détaillée du problème...",
    "location": "Tribunal de première instance",
    "commune": "Cotonou",
    "incident_date": "2024-01-10",
    "incident_time": "14:30:00",
    "is_anonymous": false,
    "contact_allowed": true,
    "attachments": [file1, file2]
}
```

### Créer un signalement audio (Fon)
```http
POST /reporting/audio/create/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
    "audio_file": <audio_file>,
    "duration": 120,
    "consent_given": true,
    "is_anonymous": false
}
```

### Résumé des signalements utilisateur
```http
GET /reporting/summary/
Authorization: Bearer <access_token>
```

**Réponse :**
```json
{
    "total_reports": 3,
    "text_reports": [
        {
            "id": 1,
            "report_id": "abc123",
            "title": "Difficulté d'accès au tribunal",
            "problem_type": "JUSTICE",
            "status": "PENDING",
            "created_at": "2024-01-15T10:00:00Z"
        }
    ],
    "audio_reports": [
        {
            "id": 1,
            "report_id": "def456",
            "duration_formatted": "02:00",
            "status": "PENDING",
            "created_at": "2024-01-14T15:30:00Z"
        }
    ],
    "pending_count": 2,
    "resolved_count": 1
}
```

## Codes d'erreur

### Erreurs d'authentification
- `400` - Données invalides
- `401` - Token manquant ou invalide
- `403` - Accès interdit

### Erreurs de validation
- `400` - Champs requis manquants
- `400` - Format de données incorrect
- `409` - Conflit (ex: utilisateur existe déjà)

### Erreurs serveur
- `500` - Erreur interne du serveur
- `503` - Service temporairement indisponible

## Limites et quotas

### Taille des fichiers
- **Images/Documents** : 10 MB maximum
- **Audio** : 50 MB maximum (3 minutes max)
- **Pièces jointes** : 5 fichiers maximum par signalement

### Types de fichiers acceptés
- **Images** : JPG, PNG
- **Documents** : PDF, DOC, DOCX
- **Audio** : MP3, WAV, M4A, AAC

### Limites de requêtes
- **Quiz** : Tentatives illimitées
- **Audio progress** : 1 mise à jour par seconde minimum
- **Signalements** : Suppression possible dans les 24h seulement

## Exemples d'intégration

### JavaScript/React Native
```javascript
// Configuration axios
const api = axios.create({
  baseURL: 'https://api.paralegal.example.com/api/',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Intercepteur pour ajouter le token
api.interceptors.request.use(config => {
  const token = AsyncStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Inscription
const register = async (userData) => {
  try {
    const response = await api.post('/auth/register/', userData);
    await AsyncStorage.setItem('access_token', response.data.tokens.access);
    await AsyncStorage.setItem('refresh_token', response.data.tokens.refresh);
    return response.data;
  } catch (error) {
    throw error.response.data;
  }
};

// Soumettre un quiz
const submitQuiz = async (quizData) => {
  try {
    const response = await api.post('/modules/quiz/submit/', quizData);
    return response.data;
  } catch (error) {
    throw error.response.data;
  }
};
```

### Flutter/Dart
```dart
import 'package:dio/dio.dart';

class ApiService {
  final Dio _dio = Dio();
  
  ApiService() {
    _dio.options.baseUrl = 'https://api.paralegal.example.com/api/';
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        String? token = await getStoredToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ));
  }
  
  Future<Map<String, dynamic>> register(Map<String, dynamic> userData) async {
    try {
      Response response = await _dio.post('/auth/register/', data: userData);
      return response.data;
    } catch (e) {
      throw e;
    }
  }
  
  Future<List<dynamic>> getModules() async {
    try {
      Response response = await _dio.get('/modules/');
      return response.data;
    } catch (e) {
      throw e;
    }
  }
}
```

## Tests et validation

### Collection Postman
L'API inclut une collection Postman complète pour tester tous les endpoints :

```json
{
    "info": {
        "name": "Paralegal API",
        "description": "Collection complète pour l'API Paralegal"
    },
    "auth": {
        "type": "bearer",
        "bearer": [
            {
                "key": "token",
                "value": "{{access_token}}"
            }
        ]
    }
}
```

### Variables d'environnement Postman
```json
{
    "base_url": "http://127.0.0.1:8000/api",
    "access_token": "",
    "refresh_token": "",
    "user_id": ""
}
```

## Webhooks et notifications

### Événements disponibles
- `user.registered` - Nouvel utilisateur inscrit
- `module.completed` - Module terminé
- `quiz.passed` - Quiz réussi
- `certificate.generated` - Certificat généré
- `report.submitted` - Signalement soumis

### Configuration webhook
```http
POST /admin/webhooks/
Authorization: Bearer <admin_token>

{
    "url": "https://your-app.com/webhook",
    "events": ["certificate.generated", "report.submitted"],
    "secret": "webhook_secret_key"
}
```

## Support et ressources

### Documentation interactive
- **Swagger UI** : `https://api.paralegal.example.com/docs/`
- **ReDoc** : `https://api.paralegal.example.com/redoc/`

### Environnements
- **Production** : `https://api.paralegal.example.com/`
- **Staging** : `https://staging-api.paralegal.example.com/`
- **Développement** : `http://127.0.0.1:8000/`

### Contact technique
- **Email** : tech@paralegal.example.com
- **WhatsApp** : +229 01 57 57 51 67
- **Documentation** : https://docs.paralegal.example.com