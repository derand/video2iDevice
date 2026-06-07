# -*- coding: utf-8 -*-
"""iTunes metadata tagging mixin for Video2iDevice."""

import os
import re
import shutil
from typing import Optional, Dict, Any, Tuple

from v2d.settings import STTNGS, atomicParsleyOptions
from v2d_utils import AtomicParsley_path


class TaggingMixin:
    """Mixin providing iTunes metadata tagging via AtomicParsley."""

    def getLang(self, i: int, lng: Optional[str] = None) -> Tuple[str, int]:
        """Return the language code for track index *i* and the next index.

        Args:
            i: Current language index into the colon-separated STTNGS lang list.
            lng: Fallback language string from the stream's own metadata.

        Returns:
            A 2-tuple ``(language_code, next_index)``.
        """
        langs = STTNGS['lang'].split(':')
        if len(langs) > i and langs[i] != '':
            return (langs[i], i + 1)
        if lng is None or lng == '':
            return ('und', i + 1)
        return (lng, i + 1)

    def tagTrackInfo(self, fn: str) -> Dict[str, Any]:
        """Extract track/season tagging metadata from a filename.

        Args:
            fn: Filename (basename is sufficient) to inspect.

        Returns:
            A dict with at least ``'track'`` and ``'tracks'`` keys, and
            optionally ``'season'``.
        """
        srch = None
        tr = None
        rv = {}
        if 'track' in STTNGS:
            tr = int(STTNGS['track'])
        if 'TRACK_REGEX' in STTNGS:
            for p in STTNGS['TRACK_REGEX']:
                srch = re.compile(p).search(fn)
                if srch is not None:
                    break
            if srch is not None:
                tr = int(srch.groups()[0]) + STTNGS['add2TrackIdx']
        rv['track'] = tr
        trs = None
        if 'tracks' in STTNGS:
            trs = int(STTNGS['tracks'])
        if 'TRACKS_REGEX' in STTNGS:
            for p in STTNGS['TRACKS_REGEX']:
                srch = re.compile(p).search(fn)
                if srch is not None:
                    break
            if srch is not None:
                trs = int(srch.groups()[0])
        rv['tracks'] = trs
        if tr is None and 'season' not in rv:
            srch = re.compile(r'[sS](\d{2})[eE](\d{2})').search(fn)
            if srch is not None:
                tr = int(srch.groups()[1]) + STTNGS['add2TrackIdx']
                rv['track'] = tr
                rv['season'] = int(srch.groups()[0])
        return rv

    def _has_iTunMOVI(self) -> bool:
        rv = 'copy_warning' in STTNGS or 'studio' in STTNGS
        for key in self._iTunMOVI_arrayKeys:
            rv = rv or len(STTNGS[key]) > 0
        return rv

    def _iTunMOVI_XML(self) -> str:
        rv = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
              "<!DOCTYPE plist PUBLIC \"-//Apple Computer//DTD PLIST 1.0//EN\" "
              "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
              "<plist version=\"1.0\">\n  <dict>\n")
        if 'copy_warning' in STTNGS:
            rv += "    <key>copy-warning</key>\n    <string>%s</string>\n" % STTNGS['copy_warning']
        if 'studio' in STTNGS:
            rv += "    <key>studio</key>\n    <string>%s</string>\n" % STTNGS['studio']
        for tag in self._iTunMOVI_arrayKeys:
            if len(STTNGS[tag]) > 0:
                rv += "    <key>%s</key>\n    <array>\n" % tag
                for name in STTNGS[tag]:
                    rv += "      <dict>\n        <key>name</key>\n        <string>%s</string>\n      </dict>\n" % name
                rv += "    </array>\n"
        rv += "  </dict>\n</plist>\n"
        return rv

    def tag_file(self, fn: str, source_fn: Optional[str] = None) -> None:
        """Tag an MP4/M4V file with iTunes metadata using AtomicParsley.

        Args:
            fn: Path to the output MP4/M4V file to tag.
            source_fn: Path to the original source file, used for TRACK_REGEX
                matching. Falls back to fn when not provided.
        """
        if not STTNGS['tn']:
            prms = {
                'encodingTool': STTNGS['encodingTool'],
            }
            info = self.tagTrackInfo(source_fn or fn)
            for option in atomicParsleyOptions:
                if option in STTNGS:
                    prms[option] = STTNGS[option]

            (track, tracks) = (info['track'], info['tracks'])
            if track is not None:
                if tracks is not None:
                    prms['tracknum'] = '%d/%d' % (track, tracks)
                    prms['TVEpisodeNum'] = '%d' % track
                else:
                    prms['tracknum'] = '%d' % track
                    prms['TVEpisodeNum'] = '%d' % track
                if 'episodes_titles' in STTNGS and len(STTNGS['episodes_titles']) > (track - 1):
                    title = '%s' % STTNGS['episodes_titles'][track - 1].replace("`", '_')
                    prms['TVEpisode'] = title
                    prms['title'] = title
                elif 'episodes' in STTNGS and len(STTNGS['episodes']) > (track - 1):
                    epInfo = STTNGS['episodes'][track - 1]
                    for option in atomicParsleyOptions:
                        if option in epInfo:
                            if option == 'title':
                                prms['TVEpisode'] = '%s' % epInfo[option]
                            prms[option] = '%s' % epInfo[option]
                else:
                    title = os.path.basename(fn)
                    title = os.path.splitext(title)[0]
                    prms['TVEpisode'] = '%s' % title

            cmd = [AtomicParsley_path, fn, ]
            for p in list(prms.keys()):
                cmd.append('--%s' % p)
                cmd.append(prms[p])
            if self._has_iTunMOVI():
                xml = self._iTunMOVI_XML()
                cmd.append('--rDNSatom')
                cmd.append(xml)
                cmd.append('name=iTunMOVI')
                cmd.append('domain=com.apple.iTunes')
            cmd.append('--overWrite')
            self._exeCmd(cmd)

    def buildFN(self, baseFN: str, convertFN: str) -> str:
        """Expand template tokens in *convertFN* using metadata from *baseFN*.

        Supported tokens: ``[NAME]``, ``[2EID]``, ``[2EC]``.

        Args:
            baseFN: Source filename used to resolve track info tokens.
            convertFN: Template filename string that may contain tokens.

        Returns:
            The expanded filename string.
        """
        rv = convertFN
        if rv.find('[NAME]') > -1:
            nm = '.'.join(os.path.basename(baseFN).split('.')[:-1])
            rv = rv.replace('[NAME]', nm)
        info = self.tagTrackInfo(baseFN)
        (track, tracks) = (info['track'], info['tracks'])
        if rv.find('[2EID]') > -1:
            if track is not None:
                rv = rv.replace('[2EID]', '%02d' % track)
        if rv.find('[2EC]') > -1:
            if tracks is not None:
                rv = rv.replace('[2EC]', '%02d' % tracks)
        return rv

    def rename(self, fn: str) -> None:
        """Move *fn* to the path specified by STTNGS ``out_file`` (if set).

        Args:
            fn: Current path of the output file.
        """
        if 'out_file' not in STTNGS:
            return None
        name = STTNGS['out_file']
        info = self.tagTrackInfo(fn)
        (tr, trs) = (info['track'], info['tracks'])
        if name.find('[SEASON]') > -1:
            if 'TVSeasonNum' in STTNGS:
                name = name.replace('[SEASON]', STTNGS['TVSeasonNum'])
        if name.find('[EPISODE_ID]') > -1:
            if tr is not None:
                name = name.replace('[EPISODE_ID]', '%02d' % tr)
        if name.find('[EPISODE_COUNT]') > -1:
            if trs is not None:
                name = name.replace('[EPISODE_COUNT]', '%02d' % trs)
        if name.find('[NAME]') > -1:
            if tr is not None:
                if 'episodes_titles' in STTNGS and len(STTNGS['episodes_titles']) > (tr - 1):
                    name = name.replace('[NAME]', STTNGS['episodes_titles'][tr - 1])
        self._printCmd('mv "%s" "%s"' % (fn, name))
        shutil.move(fn, name)
