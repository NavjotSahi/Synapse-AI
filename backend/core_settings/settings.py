# backend/core_settings/settings.py
# Django settings for core_settings project.

import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))  # Looks for .env in backend/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-default-secret-key-for-dev-if-not-set-in-env')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True' # Default to True if not set

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions', # Optional, ensure you use it or remove
    
    'rest_framework',
    'rest_framework.authtoken', # For DRF's built-in token auth (dj-rest-auth can also manage this)
    'corsheaders', # Uncomment and configure if Streamlit is on a different port/domain
    
    'django.contrib.sites', # Required by allauth, place before allauth apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount', # Optional: if you plan to add social login later
    
    'dj_rest_auth',
    'dj_rest_auth.registration',
    
    # 'rest_framework_simplejwt.token_blacklist', # Add this if SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] = True

    # Your local apps
    'api', # Or whatever your main API app is called
    # ... other apps
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 
    'corsheaders.middleware.CorsMiddleware', # If using corsheaders, place it high, often before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware', 
]

ROOT_URLCONF = 'core_settings.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Optional: if you have project-level templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request', # Required by allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core_settings.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'student_dashboard_db'),
        'USER': os.getenv('DB_USER', 'your_db_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'your_db_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Media files (User-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'media_files')
os.makedirs(MEDIA_ROOT, exist_ok=True)


SITE_ID = 1 

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication', # Primary for web clients using JWT in cookies
        # 'rest_framework_simplejwt.authentication.JWTAuthentication', # If you also need header-based JWT for other APIs
        # 'rest_framework.authentication.SessionAuthentication', # Useful for browsable API during dev
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated', # Protect endpoints by default
    ),
    # 'DEFAULT_RENDERER_CLASSES': ( # Optional: if you want JSON to be the default for browsable API
    #     'rest_framework.renderers.JSONRenderer',
    #     'rest_framework.renderers.BrowsableAPIRenderer',
    # )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # For collectstatic in production
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')] # If you have project-level static files

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT Configuration (SIMPLE_JWT settings are used by dj_rest_auth when USE_JWT=True)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60), 
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),    
    "ROTATE_REFRESH_TOKENS": False, # Set to False for simplicity to avoid blacklist app for now
    "BLACKLIST_AFTER_ROTATION": False, # If ROTATE_REFRESH_TOKENS is True and this is True, add 'rest_framework_simplejwt.token_blacklist' to INSTALLED_APPS
    "UPDATE_LAST_LOGIN": True,  
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY, # Uses Django's SECRET_KEY
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",), 
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5), 
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1), 
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend', # Needed for Django admin login
    'allauth.account.auth_backends.AuthenticationBackend', # allauth specific authentication methods
]

# dj-rest-auth settings
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'coursecompanion-auth',      # Name of the access token cookie
    'JWT_AUTH_REFRESH_COOKIE': 'coursecompanion-refresh', # Name of the refresh token cookie
    'JWT_AUTH_HTTPONLY': True,  # Recommended: True (cookie not accessible via JS)
    'JWT_AUTH_SAMESITE': 'Lax', # Or 'Strict' or 'None' (if cross-site with HTTPS)
    'SESSION_LOGIN': False,     # Set to False if you only want JWT based auth (no Django sessions for API)
    'OLD_PASSWORD_FIELD_ENABLED': True, # To enable old password field in password change
    'LOGOUT_ON_PASSWORD_CHANGE': True, # Logs out user on password change
    'USER_DETAILS_SERIALIZER': 'api.serializers.CustomUserDetailsSerializer', 
    'REGISTER_SERIALIZER': 'api.serializers.CustomRegisterSerializer', # If you need to customize registration
}

# django-allauth specific settings
ACCOUNT_LOGIN_METHODS = {'username', 'email'} # Allow login with username or email
ACCOUNT_USERNAME_REQUIRED = True # Makes username field required in forms/validation
ACCOUNT_EMAIL_REQUIRED = True    # Makes email field required
ACCOUNT_EMAIL_VERIFICATION = 'none' # FOR EASIER INITIAL TESTING. Change to 'mandatory' or 'optional' later.
                                    # 'mandatory': user must verify email to log in
                                    # 'optional': user can log in but is prompted
                                    # 'none': no email verification needed
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
ACCOUNT_CONFIRM_EMAIL_ON_GET = True # Allows email verification by clicking a link (GET request) - relevant if verification is not 'none'
LOGIN_URL = '/api/auth/login/' # Default URL for login, used by @login_required decorator if user not authenticated
# ACCOUNT_LOGOUT_ON_GET = True # Optional: Allows logout via GET request (less secure than POST)
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[CourseCompanionAI] ' # Prefix for emails sent by allauth
ACCOUNT_DEFAULT_HTTP_PROTOCOL = os.getenv('ACCOUNT_DEFAULT_HTTP_PROTOCOL', 'http') # 'http' for dev, 'https' for prod

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' # Prints emails to console during development
# For production, configure a real email backend like SMTP:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@example.com'
# EMAIL_HOST_PASSWORD = 'your-email-password'
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Ensure SECRET_KEY is properly loaded (especially important if not using the default fallback)
if SECRET_KEY == 'your-default-secret-key-for-dev-if-not-set-in-env':
    print("WARNING: Using default SECRET_KEY. Please set DJANGO_SECRET_KEY in your .env file for production.")
elif not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set. Please check your .env file or environment variables.")

# CORS settings (Uncomment and configure if your Streamlit app is on a different origin)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8501", # Example: Streamlit default dev port
    "http://127.0.0.1:8501",
]
CORS_ALLOW_CREDENTIALS = True # Important if you're using cookies (like JWT cookies) across origins