#!/usr/bin/env python3

import argparse
import os
import re
import logging
import mutagen.mp3

mr_logger = logging.getLogger(__name__)
logging.captureWarnings(True)


class Mp3File:
    def __init__(self, file_path):
        self.file_path = file_path
        self.performer, self.album, self.title = self.get_track_info(file_path)
        if len(self.performer) < 2:
            mr_logger.info('Performer tag for file {} is fishy. Trying to guess it'.format(os.path.basename(file_path)))
            self.performer = self.guess_track_info(file_path, 'performer')
        if len(self.album) < 2:
            mr_logger.info('Album tag for file {} is fishy. Trying to guess it'.format(os.path.basename(file_path)))
            self.album = self.guess_track_info(file_path, 'album')
        if len(self.title) < 2:
            mr_logger.info('Title tag for file {} is fishy. Trying to guess it'.format(os.path.basename(file_path)))
            self.title = self.guess_track_info(file_path, 'title')
        mr_logger.debug('{f} is identified as {p} - {a} - {t}'.format(f=os.path.basename(file_path), p=self.performer,
                                                                      a=self.album, t=self.title))

    @staticmethod
    def guess_track_info(mp3file, what_is_missing):
        return ''  # TODO: implement guessing logic

    @staticmethod
    def get_track_info(mp3file):
        try:
            mp3tags = mutagen.mp3.MP3(mp3file)
            _track_performer = str(mp3tags.get(key='TPE1'))
            _track_album = str(mp3tags.get(key='TALB'))
            _track_title = str(mp3tags.get(key='TIT2'))
            return _track_performer, _track_album, _track_title
        except Exception as e:
            mr_logger.info('Unable to read IDv3 tags, going to use file name and dir structure', e)
            return '', '', ''


def rearrange_files(_params, _lib):
    if _params['move_to'] == _params['target_dir'] and _params['dir_structure'] == 'plain':
        _new_path = os.path.join(os.path.dirname(_params['target_dir']), '{}.mp3'.format(mp3.title))  # TODO: rewrite.
        mr_logger.debug('Moving to {}'.format(_new_path))
        try:
            if os.path.exists(os.path.dirname(_new_path)):
                os.rename(mp3.file_path, _new_path)
            else:
                os.makedirs(os.path.dirname(_new_path))
                os.rename(mp3.file_path, _new_path)
        except Exception as e:
            mr_logger.exception("Couldn't move file {} to {}\n{}".format(mp3.file_path, _new_path, e))


def scan_dir_for_media(_p):
    if 'lib' not in _p.keys():  # So this function could be invoked recursively without overwriting the _lib
        mr_logger.info('Launching a scan of {}'.format(_p['target_dir']))
        _p['lib'] = {}

    for _entry in os.scandir(_p['target_dir']):
        if _entry.is_dir(follow_symlinks=False):
            _p['target_dir'] = _entry.path
            scan_dir_for_media(_p)
        elif _entry.name.lower().endswith('.mp3'):
            _mp3_file = Mp3File(_entry.path)

            if _mp3_file.performer not in _p['lib'].keys():
                _p['lib'][_mp3_file.performer] = {_mp3_file.album: [_mp3_file]}
            else:
                if _mp3_file.album not in _p['lib'][_mp3_file.performer].keys():
                    _p['lib'][_mp3_file.performer][_mp3_file.album] = [_mp3_file]
                else:
                    _p['lib'][_mp3_file.performer][_mp3_file.album].append(_mp3_file)

    return _p['lib']


def messy_proto():
    t_string = "12    Best Of The Best. Part One. The Past. CD 8 - Electro Lights (2005) = +_  "
    t_string = re.sub(r'(\s\s+)|(\d)|([\)\(\}\{\[\]\-\_\=\+\.])', '', t_string)
    t_string = re.sub(r'(\s\s+)', ' ', t_string)

    print(t_string)


def get_args():
    cli = argparse.ArgumentParser(description='Organize mp3 collections')
    cli.add_argument('--target_dir', metavar='D', type=str, help='Specify top directory to process.')
    cli.add_argument('--move_to', metavar='M', type=str, help='Specify where to move the files')
    cli.add_argument('--do_your_thing', action='store_true', help='Without this key no harm will be done')
    cli.add_argument('--dir_structure', metavar='S', type=str, default='plain',
                     help='Arrange the files by performer or by performer and albums (plain/albums)')
    cli.add_argument('--debug', action='store_true')
    cli_args = cli.parse_args()

    if cli_args.debug:
        mr_logger.setLevel('DEBUG')
    else:
        mr_logger.setLevel('INFO')

    if cli_args.target_dir is None:
        _target_dir = os.getcwd()
        mr_logger.info("Top directory wasn't specified, so assume it's {}".format(_target_dir))
    else:
        _target_dir = cli_args.target_dir

    if cli_args.move_to is None:
        _move_to = _target_dir
        mr_logger.info("Directory where to move the files wasn't specified, so they'll be reorganized in place")
    else:
        _move_to = cli_args.move_to

    return {'target_dir': _target_dir, 'move_to': _move_to,
            'dir_structure': cli_args.dir_structure, 'green_light': cli_args.do_your_thing}


def logger_init():
    common_log_format = '[%(name)s:%(levelname)s] %(message)s'
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        fmt=common_log_format,
        datefmt='%Y%m%d:%H%M%S'
    )
    console_handler.setFormatter(console_formatter)
    mr_logger.addHandler(console_handler)


if __name__ == '__main__':
    params = get_args()

    logger_init()

    mp3_lib = scan_dir_for_media(params)

    for performer, albums in mp3_lib.items():
        for album, mp3_files in albums.items():
            for f in mp3_files:
                print('{} - {} - {}\t({})'.format(performer, album, f.title, f.file_path))