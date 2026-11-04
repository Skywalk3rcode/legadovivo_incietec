[app]

# (str) Title of your application
title = LegadoVivo

# (str) Package name
package.name = legadovivo

# (str) Package domain (needed for android/ios packaging)
package.domain = org.lasallista.legadovivo

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
# NOTA: no se incluye 'db' a propósito: la base de datos se siembra en el primer
# arranque dentro del almacenamiento privado; empaquetar una BD local podría
# filtrar datos personales del desarrollador dentro del APK.
source.include_exts = py,png,jpg,kv,atlas,json

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec,md,txt,pyc,log

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests,bin,.pytest_cache,.git,.github,docs,tools,__pycache__,.buildozer

# (str) Application versioning (method 1)
version = 2.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
# plyer y pillow NO se usan en el código: se eliminan para reducir el tamaño del APK.
requirements = python3,kivy==2.3.1,sqlite3

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# REQUISITO EXTERNO: el repositorio no incluye icon.png. Añadir un icono 512x512
# en la raíz del proyecto y descomentar la línea siguiente (si no, se usa el
# icono por defecto de python-for-android):
#icon.filename = %(source.dir)s/icon.png

# (list) Supported orientations
# Valid values: landscape, sensorLandscape, portrait, sensorPortrait, all
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

#
# Android specific
#

# (list) Permissions
# INTERNET: solo para la comprobación TCP del estado de red (8.8.8.8:53, timeout 0,5 s);
#   la app no envía ni recibe datos de usuario. Sin ella, la comprobación cae al
#   respaldo de ConnectivityManager en Android.
# ACCESS_NETWORK_STATE: consulta del estado de conectividad (ConnectivityManager).
# No se solicita ningún otro permiso: no hay cámara, ubicación, contactos, almacenamiento
# externo ni servicios de fondo.
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 33

# (str) Android NDK version to use
#android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since extra jars can slow
# down the build process.
#android.add_jars = foo.jar,bar.jar,path/to/more/*.jar

# (list) Android architectures to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
# Desactivado por seguridad: los recuerdos del legado son datos íntimos y no deben
# copiarse al servicio de copias de Android/ADB. Reponer a True si se desea backup.
android.allow_backup = False

# (str) The format used to package the app for release mode (aab or apk or aar).
# apk para distribución directa / pruebas. Para Google Play cambiar a 'aab'
# (ver sección de instrucciones AAB del informe).
android.release_artifact = apk

# (str) The format used to package the app for debug mode (apk or aar).
android.debug_artifact = apk

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug when possible)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

