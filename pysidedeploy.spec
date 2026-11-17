[app]
title = canned beer sprites
project_dir = .
input_file = canned_beer/app.py
exec_directory = dist
project_file = 
icon = 

[python]
packages = Nuitka==4.1.1
android_packages = buildozer==1.6.0,cython==0.29.33

[qt]
qml_files = 
excluded_qml_plugins = 
modules = Core,DBus,Gui,Widgets
plugins = accessiblebridge,egldeviceintegrations,generic,iconengines,imageformats,platforminputcontexts,platforms,platforms/darwin,platformthemes,styles,wayland-decoration-client,wayland-graphics-integration-client,wayland-shell-integration,xcbglintegrations

[android]
wheel_pyside = 
wheel_shiboken = 
plugins = 

[ios]
wheel_pyside = 
wheel_shiboken = 
xcframework_path = 
bundle_id = 
team_id = 
version = 1.0
deployment_target = 
entitlements = 
signing_style = Automatic
header_search_paths = 

[nuitka]
macos.permissions = 
mode = standalone
extra_args = --quiet --noinclude-qt-translations

[buildozer]
mode = debug
recipe_dir = 
jars_dir = 
ndk_path = 
sdk_path = 
local_libs = 
arch = 

