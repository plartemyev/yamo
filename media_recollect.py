#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import logging
import shutil
import mutagen.mp3
import sys

mr_logger = logging.getLogger(__name__)
logging.captureWarnings(True)

if 'scandir' not in os.__dict__:  # Python < 3.5 workaround. Of course, scandir module  should be installed in such case.
    try:
        import scandir
        os.scandir = scandir.scandir
    except Exception as e:
        mr_logger.error('Unable to use built-in function "os.scandir" or import it from a separate module. \
            Please use Python>=3.5 or install "scandir" with pip.')
        sys.exit(1)


class Mp3File:
    def __init__(self, file_path):
        self.file_path = file_path
        self.performer = ''
        self.album = ''
        self.title = ''
        self.index = 0
        self.year = 0
        self.get_track_info()
        mr_logger.debug('{f} is identified as {p} - {a} - {t}, year {y}, index {i}'
                        .format(f=os.path.basename(self.file_path), p=self.performer, a=self.album, t=self.title,
                                y=self.year, i=self.index))

        MediaAlbum.handle(self)

    def guess_info(self, *what_is_missing: str) -> list:
        _pieces = []
        mr_logger.info('Unable to read IDv3 tags, trying other means of identification ({})'.format(self.file_path))

        # TODO: implement alternate identification (fingerprints) and guessing logic
        for _piece in what_is_missing:
            _pieces.append(None)

        if any([_i is None for _i in _pieces]):
            raise UserWarning('Unidentified track', self.file_path)

        return _pieces

    def get_track_info(self):
        try:
            mp3tags = mutagen.mp3.MP3(self.file_path)
            _performer = mp3tags.get(key='TPE2')
            _album = mp3tags.get(key='TALB')
            _title = mp3tags.get(key='TIT2')
            _year = mp3tags.get(key='TDRC')
            _index = mp3tags.get(key='TRCK')

            if not _performer:
                _performer = mp3tags.get(key='TPE1')  # Try to use Track performer if Album Performer is empty.

            if not any([_performer, _album, _title]):  # No data at all
                _performer, _album, _title, _year, _index = self.guess_info(
                    'performer', 'album', 'title', 'year', 'index')

            if _index:
                _i = str(_index)
                if _i.isdigit():
                    self.index = int(_i)
                else:
                    _i = re.split(r'[^0-9]', _i, 1)[0]
                    if _i.isdigit():
                        self.index = int(_i)

            if _year:
                _i = str(_year)
                if _i.isdigit():
                    self.year = int(_i)
                else:
                    _i = re.split(r'[^0-9]', _i, 1)[0]
                    if _i.isdigit():
                        self.year = int(_i)

            if _performer and len(str(_performer)) < 2:
                mr_logger.info('Performer tag for file {} is fishy. Trying to guess it'.format(self.file_path))
                _performer = self.guess_info('performer')
            if _album and len(str(_album)) < 2:
                mr_logger.info('Album tag for file {} is fishy. Trying to guess it'.format(self.file_path))
                _album = self.guess_info('album')
            if _title and len(str(_title)) < 2:
                mr_logger.info('Title tag for file {} is fishy. Trying to guess it'.format(self.file_path))
                _track_title = self.guess_info('title')

            self.performer = str(_performer).replace('&', 'and')  # To fight 'A & B' != 'A and B'
            self.album = str(_album).replace('&', 'and')
            self.title = str(_title).replace('&', 'and')

        except Exception as e:
            raise

    @staticmethod
    def cleanup_string(_s: str) -> str:
        _staging_s = re.sub(r'[^a-zA-Z0-9 ._-]', '', _s)
        _staging_s = re.sub(r'(\s\s+)', ' ', _staging_s)
        _staging_s = _staging_s.strip(' .')
        _staging_s = _staging_s.strip()  # just to be safe of non-standard space chars.
        return _staging_s


class MediaAlbum:
    albums = {}  # Storage for all instances of this class

    @classmethod
    def handle(cls, track: Mp3File):  # Not exactly a factory method. Returns appropriate instance of MediaAlbum object
        if track.performer in cls.albums.keys():
            if track.album in cls.albums[track.performer].keys():
                cls.albums[track.performer][track.album].compositions = track
                return cls.albums[track.performer][track.album]
        return cls(track)

    @classmethod
    def get_performers(cls) -> list:
        return list(cls.albums.keys())

    @classmethod
    def get_albums_for_performer(cls, performer: str) -> list:
        return list(cls.albums[performer].items()[1])

    def __init__(self, track: Mp3File):
        self.name = track.album
        self.performer = track.performer
        self.year = track.year
        self.index = 0
        self._compositions = [track]
        if self.performer not in self.albums.keys():
            self.albums[self.performer] = {self.name: self}
        else:
            self.albums[self.performer][self.name] = self
            self.reindex_albums()

    @property
    def compositions(self) -> list:
        return self._compositions

    @compositions.setter
    def compositions(self, track: Mp3File):
        if track.year > self.year:
            self.year = track.year
            self.reindex_albums()
        self._compositions.sort(key=lambda _k: _k.index)
        self._compositions.append(track)

    def reindex_albums(self):
        _albums_by_year = sorted(self.albums[self.performer].values(), key=lambda _k: _k.year)
        for _index, _album in enumerate(_albums_by_year, 1):
            self.albums[self.performer][_album.name].index = _index


class MediaLib:
    def __init__(self, files: list):
        self.multiple_performers = False
        for path in files:
            try:
                Mp3File(path)  # Just initializing it.
            except Exception as e:
                if isinstance(e, UserWarning):
                    mr_logger.warning('Unable to identify media file, skipping it. {}'.format(e.args[1]))
                else:
                    mr_logger.warning('Something unexpected happened while examining the file {}. Skipping. {}'
                                      .format(path, e))
                continue

    def check_multiple_performers_presence(self):
        if len(MediaAlbum.albums) > 1:
            self.multiple_performers = True
            mr_logger.info('Multiple performers detected in the source directory')

    @staticmethod
    def get_performers() -> tuple:
        return tuple(MediaAlbum.albums.keys())

    @staticmethod
    def get_albums(*args) -> tuple:
        _albums = []
        if args:
            for requested_performer in args:
                for album in MediaAlbum.albums[requested_performer]:
                    _albums.append(album)
        else:
            for performer in MediaAlbum.albums:
                for album in MediaAlbum.albums[performer]:
                    _albums.append(album)
        return tuple(_albums)

    @staticmethod
    def get_tracks(**kwargs) -> tuple:
        _tracks = []

        if not kwargs:
            for performer in MediaAlbum.albums:
                for album in MediaAlbum.albums[performer]:
                    _tracks.extend(MediaAlbum.albums[performer][album].compositions)
            return tuple(_tracks)

        for request in kwargs:
            if request == 'performers':
                for requested_performer in kwargs['performers']:
                    for album in MediaAlbum.albums[requested_performer]:
                        _tracks.extend(MediaAlbum.albums[requested_performer][album].compositions)
                return tuple(_tracks)

            if request == 'albums':
                for requested_album in kwargs['albums']:
                    for performer in MediaAlbum.albums:
                        for album in MediaAlbum.albums[performer]:
                            if requested_album in album:
                                _tracks.extend(MediaAlbum.albums[performer][album].compositions)
                return tuple(_tracks)

    @staticmethod
    def straighten_performers_line():
        _initial_performers = set(MediaAlbum.albums.keys())
        _messy_performer_tags = []
        for _p in _initial_performers:
            for _o in filter(lambda _o: _o != _p, _initial_performers):
                if _p in _o:  # "TPE2: Katy B x Diplo x Iggy Azaelia".
                    mr_logger.debug('Messy album performer tag encountered. Correcting it from "{}" to "{}"'
                                    .format(_o, _p))
                    _messy_performer_tags.append(_o)
                    for _alb in MediaAlbum.albums[_o].keys():
                        for composition in MediaAlbum.albums[_o][_alb].compositions:
                            composition.performer = _p
                            MediaAlbum.handle(composition)

        for _messy_performer in set(_messy_performer_tags):
            del MediaAlbum.albums[_messy_performer]
        if len(_initial_performers) > len(set(MediaAlbum.albums.keys())):
            mr_logger.info('Performers were streamlined from "{}" to "{}"\n'
                           .format(_initial_performers, set(MediaAlbum.albums.keys())))

    def process_file(self, _p: dict, _album: MediaAlbum, _track: Mp3File) -> str:
        _c_performer = Mp3File.cleanup_string(_album.performer)
        _c_alb_name = Mp3File.cleanup_string(_album.name)
        _c_trck_title = Mp3File.cleanup_string(_track.title)
        if any((_album.performer != _c_performer, _album.name != _c_alb_name, _track.title != _c_trck_title)):
            mr_logger.debug('Names to be used in file path were cleared. From "{}" "{}" "{}"\nto "{}" "{}" "{}"'
                            .format(_album.performer, _album.name, _track.title,
                                    _c_performer, _c_alb_name, _c_trck_title))

        if self.multiple_performers:
            _target_dir = os.path.join(_p['target_dir'], _c_performer)
        else:
            _target_dir = _p['target_dir']

        if _target_dir == _p['source_dir'] and _p['dir_structure'] == 'plain':
            # mr_logger.debug('In-place files reorganization - "0101 Track_name.extension" - first 01 is an Album index')
            if _p['no_indexes']:
                _new_name = '{}.mp3'.format(_c_trck_title)
            else:
                _new_name = '{:02d}{:02d} {}.mp3'.format(_album.index, _track.index, _c_trck_title)
            _new_path = os.path.join(_target_dir, _new_name)

        elif _target_dir == _p['source_dir'] and _p['dir_structure'] == 'albums':
            # mr_logger.debug('In-place files reorganization - "Album_year Album_name/01 Track_name.extension"')
            if _p['no_indexes']:
                _new_name = '{}.mp3'.format(_c_trck_title)
            else:
                _new_name = '{:02d} {}.mp3'.format(_track.index, _c_trck_title)
            _new_path = os.path.join(_target_dir, '{} {}'.format(_album.year, _c_alb_name), _new_name)

        elif _target_dir != _p['source_dir'] and _p['dir_structure'] == 'plain':
            # mr_logger.debug('Total reorganization - "Performer/0101 Track_name.extension" - first 01 is an Album index')
            if _p['no_indexes']:
                _new_name = '{}.mp3'.format(_c_trck_title)
            else:
                _new_name = '{:02d}{:02d} {}.mp3'.format(_album.index, _track.index, _c_trck_title)
            _new_path = os.path.join(_target_dir, _new_name)

        elif _target_dir != _p['source_dir'] and _p['dir_structure'] == 'albums':
            # mr_logger.debug('Total reorganization - "Performer/Album_year Album_name/01 Track_name.extension"')
            if _p['no_indexes']:
                _new_name = '{}.mp3'.format(_c_trck_title)
            else:
                _new_name = '{:02d} {}.mp3'.format(_track.index, _c_trck_title)
            _new_path = os.path.join(_target_dir, '{} {}'.format(_album.year, _c_alb_name), _new_name)

        else:
            if _p['no_indexes']:
                _new_name = '{}.mp3'.format(_c_trck_title)
            else:
                _new_name = '{:02d}{:02d} {}.mp3'.format(_album.index, _track.index, _c_trck_title)
            _new_path = os.path.join(_target_dir, _new_name)
            mr_logger.warning('Unrecognized file layout requested. Using {}'.format(_new_path))

        if _track.file_path == _new_path:
            #  Normally this shouldn't happen
            mr_logger.warning('Duplicated file encountered - {}'.format(_new_path))

        mr_logger.info('Processing {} to {}\n'.format(_track.file_path, _new_path))

        try:
            if _p['op_mode'] in ('move', 'copy') and not os.path.exists(os.path.dirname(_new_path)):
                os.makedirs(os.path.dirname(_new_path))

            if _p['op_mode'] == 'move':
                shutil.move(_track.file_path, _new_path)
                return _new_path

            elif _p['op_mode'] == 'copy' and _target_dir != _p['source_dir']:
                shutil.copy2(_track.file_path, _new_path)
                return _new_path

            else:
                # Dry run mode - return suggested new path and do nothing
                return _new_path

        except Exception as e:
            mr_logger.exception("Couldn't process file {} to {}\n{}\n".format(_track.file_path, _new_path, e))


def scan_dir_for_media(_source_dir, _file_list):
    try:
        for _entry in os.scandir(_source_dir):
            if _entry.is_dir(follow_symlinks=False):
                _source_dir = _entry.path
                scan_dir_for_media(_source_dir, _file_list)
            elif _entry.name.lower().endswith('.mp3'):
                _file_list.append(_entry.path)

        return _file_list
    except PermissionError:
        mr_logger.warning(sys.exc_info()[1])


def get_args():
    cli = argparse.ArgumentParser(description='Organize mp3 collections')
    cli.add_argument('--source_dir', type=str,
                     help='Specify source directory to process. Current directory used if omitted.')
    cli.add_argument('--target_dir', type=str,
                     help='Specify where to move the files. "source_dir" used if omitted.')
    cli.add_argument('--op_mode', type=str, default='no-op',
                     help='Mode of operation (no-op/copy/move). "no-op" if omitted.')
    cli.add_argument('--dir_structure', type=str, default='plain',
                     help='Arrange the files by performer or by performer and albums (plain/albums). Plain if omitted.')
    cli.add_argument('--no_indexes', action='store_true',
                     help='Do not prefix media files with any indexes. Indexes on if omitted.')
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
            'op_mode': cli_args.op_mode, 'no_indexes': cli_args.no_indexes}


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

    m_lib = MediaLib(mp3_files)
    m_lib.straighten_performers_line()
    m_lib.check_multiple_performers_presence()

    for performer in m_lib.get_performers():
        for album in m_lib.get_albums(performer):
            for _track in MediaAlbum.albums[performer][album].compositions:
                m_lib.process_file(params, MediaAlbum.albums[performer][album], _track)
