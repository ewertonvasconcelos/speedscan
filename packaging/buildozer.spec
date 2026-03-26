[app]

# (str) Title of your application
title = SpeedScan

# (str) Package name
package.name = speedscan

# (str) Package domain (needed for android/ios packaging)
package.domain = org.speedscan

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/images/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/images/icon.png

# (list) Supported orientations
# Valid options are: landscape, portrait, portrait-reverse or landscape-reverse
orientation = portrait

#
# (list) List of modules to add as python android modules
# android.modules = android

#
# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

#
# Android specific
#

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 23b

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid excess Internet downloads or save time
# if an update is due and you just want to test/build your package
android.skip_update = False

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.renpy.android.PythonActivity

# (list) Android application meta-data to set (key=value format)
#android.meta_data =

# (list) Android library project to add (will be added in Gradle project)
#android.library_references =

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.arch = armeabi-v7a

#
# iOS specific
#

# (str) Path to a custom kivy-ios directory
#ios.kivy_ios_dir = ../kivy-ios

# (str) Name of the certificate to use for signing the debug version on iOS
#ios.codesign.debug = ?

# (str) Name of the certificate to use for signing the release version on iOS
#ios.codesign.release = ?

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
bin_dir = ./bin
