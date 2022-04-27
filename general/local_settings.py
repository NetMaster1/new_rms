# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-r4mqhl#nt7-joaq(9x_h3n&s62xq3qa)#&^kphc7!-jkga)gw6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [ '127.0.0.1','e-rms.ru', 'www.e-rms.ru']

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': BASE_DIR / 'db.sqlite3',
        'ENGINE':   'django.db.backends.postgresql',
            'NAME': 'new_rms',
            'USER': 'postgres',
            'PASSWORD': 'ylhio65v',
            'HOST': 'localhost',
            'PORT': '5432'
    }
}
