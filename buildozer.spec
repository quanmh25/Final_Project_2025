[app]
# Basic app info
title = Our project
package.name = myapp
package.domain = org.test
version = 0.1

# Source configuration
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
orientation = portrait

# Requirements
requirements = python3,kivy,sqlite3,plyer,android

[android]
# API settings
minapi = 21
ndk = 23b
api = 31

# Permissions
permissions = INTERNET, VIBRATE, RECEIVE_BOOT_COMPLETED

# Build settings
archs = arm64-v8a, armeabi-v7a
allow_backup = False
release_artifact = apk

[buildozer]
log_level = 2