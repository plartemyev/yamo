import argparse
import os
import re
import logging
import mutagen.mp3


mr_logger = logging.getLogger(__name__)
logging.captureWarnings(True)

class Mp3File:
    def __init__(self, filepath):
        self.title = self.get_title()
        self.album = self.get_album()
        self.performer = self.get_performer()

    def get_title(self):
        return ''

    def get_album(self):
        return ''

    def get_performer(self):
        return ''


def get_tags(filepath):
    audio = mutagen.mp3.MP3(filepath)
    t_album = audio.get(key="TALB")
    t_track_title = audio.get(key="TIT2")
    return t_album, t_track_title


for root, dirs, files in os.walk(topdir):
    for file in files:
        if file.lower().endswith(".mp3"):
            s_artist = os.path.basename(topdir)
            s_album = os.path.basename(root)
            mp3_filename = file
            mp3_filepath = os.path.join(root, file)
            t_album, t_track_title = get_tags(mp3_filepath)
            print("Processing ", "'", mp3_filename, "'", "...", sep='')
            print("Album: ", t_album, "; ", "Track title: ", t_track_title, sep='')

t_string = "    Best Of The Best. Part One. The Past. CD 8 - Electro Lights (2005) = +_  "
t_string = re.sub(r'(\s\s+)|(\d)|([\)\(\}\{\[\]\-\_\=\+\.])', '', t_string)
t_string = re.sub(r'(\s\s+)', ' ', t_string)

print(t_string)

def get_args():
    cli = argparse.ArgumentParser(description='Organize mp3 collections')
    cli.add_argument('topdir', metavar='T', type=str, nargs='?',
                     help='Specify top directory to proceed.')
    cli.add_argument('--debug', action='store_true')
    return cli.parse_args()


if __name__ == 'main':
    cli_args = get_args()

    common_log_format = '[%(name)s:%(levelname)s] %(message)s'
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        fmt=common_log_format,
        datefmt='%Y%m%d:%H%M%S'
    )
    console_handler.setFormatter(console_formatter)
    mr_logger.addHandler(console_handler)
    if cli_args.debug:
        mr_logger.setLevel('DEBUG')
    else:
        mr_logger.setLevel('WARN')

    if cli_args.topdir is None:
        topdir = os.getcwd()
        mr_logger.warning("Top directory wasn't specified, so assume it's {}".format(topdir))
    else:
        topdir = cli_args.topdir
