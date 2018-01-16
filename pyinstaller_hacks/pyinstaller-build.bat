pyinstaller --clean -y --noupx ^
--add-data music_sort.ui;. ^
--add-data ui_resources;ui_resources ^
--runtime-hook cwd_hack.py ^
-w .\yamo.py
