#!/usr/bin/env python3

import argparse
import os
import re
import logging
import shutil

import mutagen.mp3
import sys

mr_logger = logging.getLogger(__name__)
logging.captureWarnings(True)


class Mp3File:
    def __init__(self, file_path):
        self.file_path = file_path
        self.performer, self.album, self.title, self.index, self.year = self.get_track_info(file_path)
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
            _track_performer = str(mp3tags.get(key='TPE2'))
            _track_album = str(mp3tags.get(key='TALB'))
            _track_title = str(mp3tags.get(key='TIT2'))
            _track_ind = int(str(mp3tags.get(key='TRCK')).split('/')[0])
            _track_year = int(str(mp3tags.get(key='TDRC')))
            return _track_performer, _track_album, _track_title, _track_ind, _track_year
        except Exception as e:
            mr_logger.info('Unable to read IDv3 tags, going to use other means of identification', e)
            return '', '', ''


def process_file(_p: dict, _album: dict, _media_file: Mp3File) -> str:
    if _p.get('multiple_performers', False):
        _p['target_dir'] = os.path.join(_p['target_dir'], _media_file.performer)

    if _p['target_dir'] == _p['source_dir'] and _p['dir_structure'] == 'plain':
        # In-place files reorganization to new style: 0101 Track_name.extension - first 01 is an Album index
        _new_name = '{:02d}{:02d} {}.mp3'.format(_album['index'], _media_file.index, _media_file.title)
        _new_path = os.path.join(_p['target_dir'], _new_name)

    elif _p['target_dir'] == _p['source_dir'] and _p['dir_structure'] == 'albums':
        # In-place files reorganization to new style: Album_year Album_name/01 Track_name.extension
        _new_name = '{:02d} {}.mp3'.format(_media_file.index, _media_file.title)
        _new_path = os.path.join(_p['target_dir'], '{} {}'.format(_album['year'], _album['name']), _new_name)

    elif _p['target_dir'] != _p['source_dir'] and _p['dir_structure'] == 'plain':
        # Total files reorganization to new style: Performer/0101 Track_name.extension - first 01 is an Album index
        _new_name = '{:02d}{:02d} {}.mp3'.format(_album['index'], _media_file.index, _media_file.title)
        _new_path = os.path.join(_p['target_dir'], _media_file.performer, _new_name)

    elif _p['target_dir'] != _p['source_dir'] and _p['dir_structure'] == 'albums':
        # Total files reorganization to new style: Performer/Album_year Album_name/01 Track_name.extension
        _new_name = '{:02d} {}.mp3'.format(_media_file.index, _media_file.title)
        _new_path = os.path.join(_p['target_dir'], _media_file.performer,
                                 '{} {}'.format(_album['year'], _album['name']), _new_name)

    else:
        _new_name = '{:02d}{:02d} {}.mp3'.format(_album['index'], _media_file.index, _media_file.title)
        _new_path = os.path.join(_p['target_dir'], _new_name)
        mr_logger.warning('Unrecognized file layout requested. Using {}'.format(_new_path))

    if _media_file.file_path == _new_path:
        #  Normally this shouldn't happen
        mr_logger.warning('Duplicated file encountered - {}'.format(_new_path))

    mr_logger.debug('Processing {} to {}'.format(_media_file.file_path, _new_path))

    try:
        if not os.path.exists(os.path.dirname(_new_path)):
            os.makedirs(os.path.dirname(_new_path))

        if _p['op_mode'] == 'move':
            shutil.move(_media_file.file_path, _new_path)
            return _new_path

        elif _p['op_mode'] == 'copy' and _p['target_dir'] != _p['source_dir']:
            shutil.copy2(_media_file.file_path, _new_path)
            return _new_path

        elif _p['op_mode'] == 'copy' and _p['target_dir'] == _p['source_dir']:
            mr_logger.error('Attempted to re-organize files in-place using copy op_mode. That would be a mess. Exiting')
            sys.exit(2)

        else:
            # Dry run mode - log intentions and do nothing
            mr_logger.info('Dry run mode. Wanted to process {} to {}'.format(_media_file.file_path, _new_path))
            return _new_path

    except Exception as e:
        mr_logger.exception("Couldn't process file {} to {}\n{}".format(_media_file.file_path, _new_path, e))


def scan_dir_for_media(_source_dir, _file_list):
    for _entry in os.scandir(_source_dir):
        if _entry.is_dir(follow_symlinks=False):
            _source_dir = _entry.path
            scan_dir_for_media(_source_dir, _file_list)
        elif _entry.name.lower().endswith('.mp3'):
            _file_list.append(_entry.path)

    return _file_list


def lib_processing(_p, _file_list):
    _lib = {}

    for _file in _file_list:
        _mp3_file = Mp3File(_file)

        if _mp3_file.performer not in _lib.keys():  # Initializing new performer tree
            _lib[_mp3_file.performer] = {_mp3_file.album: {'year': _mp3_file.year, 'tracks': [_mp3_file]}}
        else:
            if _mp3_file.album not in _lib[_mp3_file.performer].keys():  # Initializing new album
                _lib[_mp3_file.performer][_mp3_file.album] = {'year': _mp3_file.year, 'tracks': [_mp3_file]}
            else:  # Just adding another track
                _lib[_mp3_file.performer][_mp3_file.album]['tracks'].append(_mp3_file)
                if _mp3_file.year > _lib[_mp3_file.performer][_mp3_file.album]['year']:  # Bumping album year
                    _lib[_mp3_file.performer][_mp3_file.album]['year'] = _mp3_file.year

    for _performer, _albums in _lib.items():
        _albums_by_year = sorted(_albums.items(), key=lambda _k: _k[1]['year'])
        for _index, _album in enumerate(_albums_by_year, 1):
            _lib[_performer][_album[0]]['index'] = _index

    return _lib


def messy_proto():
    t_string = "12    Best Of The Best. Part One. The Past. CD 8 - Electro Lights (2005) = +_  "
    t_string = re.sub(r'(\s\s+)|(\d)|([\)\(\}\{\[\]\-\_\=\+\.])', '', t_string)
    t_string = re.sub(r'(\s\s+)', ' ', t_string)

    print(t_string)


def get_args():
    cli = argparse.ArgumentParser(description='Organize mp3 collections')
    cli.add_argument('--source_dir', type=str, help='Specify source directory to process.')
    cli.add_argument('--target_dir', type=str, help='Specify where to move the files')
    cli.add_argument('--op_mode', type=str, default='no-op', help='Mode of operation (no-op/copy/move/')
    cli.add_argument('--dir_structure', type=str, default='plain',
                     help='Arrange the files by performer or by performer and albums (plain/albums)')
    cli.add_argument('--debug', action='store_true')
    cli_args = cli.parse_args()

    if cli_args.debug:
        mr_logger.setLevel('DEBUG')
    else:
        mr_logger.setLevel('INFO')

    if cli_args.source_dir is None:
        _source_dir = os.getcwd()
        mr_logger.info("Source directory wasn't specified, so assume it's {}".format(_source_dir))
    else:
        _source_dir = cli_args.source_dir

    if cli_args.target_dir is None:
        _target_dir = _source_dir
        mr_logger.info("Directory where to copy/move the files wasn't specified, so they'll be reorganized in-place")
    else:
        _target_dir = cli_args.target_dir

    if cli_args.op_mode == 'copy' and _target_dir == _source_dir:
        mr_logger.error('Attempted to re-organize files in-place using copy op_mode. That would be a mess. Exiting')
        sys.exit(2)

    return {'source_dir': _source_dir, 'target_dir': _target_dir, 'dir_structure': cli_args.dir_structure,
            'op_mode': cli_args.op_mode}


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

    mp3_files = scan_dir_for_media(params['source_dir'], [])
    mp3_lib = lib_processing(params, mp3_files)
    if len(mp3_lib) > 1:
        params['multiple_performers'] = True

    for performer, albums in mp3_lib.items():
        for album, album_data in sorted(albums.items(), key=lambda _k: _k[1]['index']):
            for track in sorted(album_data['tracks'], key=lambda _k: _k.index):
                # print('{} - {} - {}\t({})\t{} {}'.format(performer, album, track.title, track.file_path,
                #                                          album_data['index'], album_data['year']))
                process_file(params, album_data, track)
