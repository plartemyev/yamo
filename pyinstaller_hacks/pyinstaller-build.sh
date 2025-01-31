#!/usr/bin/env bash

pyinstaller --clean -y \
	--add-data ../music_sort.ui:. \
	--add-data ../ui_resources:ui_resources \
	--additional-hooks-dir ../pyinstaller_hacks \
	--runtime-hook ../pyinstaller_hacks/cwd_hack.py \
	--icon ../ui_resources/icons/audio-x-generic.ico \
	-F -w ../yamo.py
