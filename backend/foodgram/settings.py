import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    default='django-insecure-c&nzzt8b)g6um2qk8c4$2msza0p0fhh^^lrp8%gv+0jz(fj5rn'
)

DEBUG = True

ALLOWED_HOSTS = [
    '51.250.6.88',
    'yatubeweb.sytes.net',
]

AUTH_USER_MODEL = 'users.User'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'users.apps.UsersConfig',
    'recipes.apps.RecipesConfig',

    'rest_framework',
    'djoser',
    'rest_framework.authtoken',
    'sorl.thumbnail',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'foodgram.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'foodgram.wsgi.application'

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR + 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv(
                'DB_ENGINE',
                default='django.db.backends.postgresql'),
            'NAME': os.getenv(
                'POSTGRES_DB',
                default='postgres'),
            'USER': os.getenv(
                'POSTGRES_USER',
                default='postgres'),
            'PASSWORD': os.getenv(
                'POSTGRES_PASSWORD',
                default='postgres'),
            'HOST': os.getenv(
                'DB_HOST',
                default='db'),
            'PORT': os.getenv(
                'DB_PORT',
                default='5432'),
        }}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'recipes.paginations.LimitPageNumberPagination',
    'PAGE_SIZE': 6
}


LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

URL_PATH = 'http://51.250.6.88'

CONSTANT_KEY_MSG = {
    'NOT_SUB_TO_YOURSELF': {'errors': 'Нельзя подписаться на себя'},
    'NOT_SUB_TO_TWICE': {'errors': 'Нельзя подписаться дважды'},
    'NOT_SUB_DELETE': {'errors': 'Нельзя отписаться от данного пользователя'},
    'USER_NOT_FOUND': {'detail': 'Несуществующий пользователь!'},
    'PASSWORD_OK': {'message': 'Пароль изменен!'},
    'NOT_RECIPE': {'detail': 'Несуществующий рецепт'},
    'NOT_FAVORITE_TO_TWICE': {'errors': 'Нельзя добавить в избранное дважды'},
    'NOT_FAVORITE_DELETE': {'errors': 'Нельзя убрать из избранного'},
    'NOT_SHOP_TO_TWICE': {'errors': 'Нельзя добавить в корзину дважды'},
    'NOT_SHOP_DELETE': {'errors': 'Нельзя убрать из корзины'},
    'SHOPPING_CART_EMPTY': {'errors': 'Корзина пуста'},
}

SHOPPING_CATR_FILENAME = 'shoppingcart.txt'
