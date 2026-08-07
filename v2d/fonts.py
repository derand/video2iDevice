# -*- coding: utf-8 -*-
"""Font discovery for subtitle tracks.

Players without a system font provider (notably VLC on Android, whose libass is
built without fontconfig) can only use fonts attached to the container. This
module finds which families a subtitle script asks for and locates the matching
files in the user's font library so they can be attached.

Matching is always done on the family name stored inside the font, never on the
file name — collections routinely contain files like ``10352_0.ttf``.
"""

import os
import re
import struct
import logging
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

FONT_EXTENSIONS = ('.ttf', '.otf', '.ttc', '.otc')

_MIME_BY_EXT = {
    '.ttf': 'application/x-truetype-font',
    '.ttc': 'application/x-truetype-font',
    '.otf': 'application/vnd.ms-opentype',
    '.otc': 'application/vnd.ms-opentype',
}

# Family names carried by every ASS script but never resolved as real fonts.
_IGNORED_FAMILIES = frozenset(['', 'default'])

_FN_TAG_RE = re.compile(r'\\fn([^\\}]*)')


def mime_type(path: str) -> str:
    """Return the attachment MIME type matching *path*'s extension."""
    return _MIME_BY_EXT.get(os.path.splitext(path)[1].lower(),
                            'application/octet-stream')


def normalize_family(name: str) -> str:
    """Normalise a family name for comparison (case, spacing, @ prefix).

    The leading ``@`` marks vertical-writing variants in ASS and is not part of
    the family name itself.
    """
    name = name.strip()
    if name.startswith('@'):
        name = name[1:]
    return ' '.join(name.split()).lower()


# ── Reading family names out of font files ────────────────────────────────────

def _decode_name_record(platform_id: int, raw: bytes) -> Optional[str]:
    """Decode one 'name' table record according to its platform."""
    encodings = ('utf-16-be', 'utf-8') if platform_id in (0, 3) else ('mac-roman', 'latin-1')
    for enc in encodings:
        try:
            text = raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
        if text and '\x00' not in text:
            return text
    return None


def _families_from_sfnt(fh, offset: int) -> Set[str]:
    """Read family names (name IDs 1 and 16) from one sfnt font at *offset*."""
    families: Set[str] = set()
    fh.seek(offset)
    header = fh.read(12)
    if len(header) < 12:
        return families
    num_tables = struct.unpack('>H', header[4:6])[0]

    name_offset = None
    for _ in range(num_tables):
        record = fh.read(16)
        if len(record) < 16:
            return families
        if record[:4] == b'name':
            name_offset = struct.unpack('>I', record[8:12])[0]
            break
    if name_offset is None:
        return families

    fh.seek(name_offset)
    head = fh.read(6)
    if len(head) < 6:
        return families
    count, string_offset = struct.unpack('>HH', head[2:6])
    records = fh.read(12 * count)
    if len(records) < 12 * count:
        return families

    for i in range(count):
        platform_id, _enc_id, _lang_id, name_id, length, rec_offset = \
            struct.unpack('>HHHHHH', records[i * 12:(i + 1) * 12])
        if name_id not in (1, 16):
            continue
        fh.seek(name_offset + string_offset + rec_offset)
        text = _decode_name_record(platform_id, fh.read(length))
        if text:
            families.add(normalize_family(text))
    families.discard('')
    return families


def font_families(path: str) -> Set[str]:
    """Return the set of normalised family names provided by a font file.

    Handles TrueType/OpenType files and collections (.ttc/.otc). Returns an
    empty set for anything unreadable — a broken font in the library must not
    abort a conversion.
    """
    try:
        with open(path, 'rb') as fh:
            tag = fh.read(4)
            if tag == b'ttcf':
                fh.seek(8)
                num_fonts = struct.unpack('>I', fh.read(4))[0]
                offsets = struct.unpack('>%dI' % num_fonts, fh.read(4 * num_fonts))
                families: Set[str] = set()
                for offset in offsets:
                    families |= _families_from_sfnt(fh, offset)
                return families
            return _families_from_sfnt(fh, 0)
    except (OSError, struct.error, ValueError) as e:
        logger.warning('cannot read font "%s": %s', path, e)
        return set()


# ── Font library index ────────────────────────────────────────────────────────

def build_index(dirs: List[str]) -> Dict[str, List[str]]:
    """Index the font library: normalised family name → list of font files.

    Directories are expanded (``~``) and scanned non-recursively; missing ones
    are skipped silently so a default like ``~/.fonts/subs`` costs nothing when
    absent.
    """
    index: Dict[str, List[str]] = {}
    for directory in dirs:
        directory = os.path.expanduser(directory)
        if not os.path.isdir(directory):
            continue
        for entry in sorted(os.listdir(directory)):
            if not entry.lower().endswith(FONT_EXTENSIONS):
                continue
            path = os.path.join(directory, entry)
            if not os.path.isfile(path):
                continue
            for family in font_families(path):
                index.setdefault(family, []).append(path)
    logger.debug('font index: %d families from %s', len(index), dirs)
    return index


# ── Reading family names out of subtitle scripts ──────────────────────────────

def families_from_ass(path: str, encoding: str = 'utf-8') -> Set[str]:
    """Return every font family an ASS/SSA script refers to.

    Covers both the ``[V4+ Styles]`` section and inline ``\\fn`` overrides.
    """
    families: Set[str] = set()
    try:
        with open(path, 'r', encoding=encoding, errors='replace') as fh:
            in_styles = False
            fields: List[str] = []
            for line in fh:
                line = line.strip()
                if line.startswith('['):
                    in_styles = line.lower().startswith(('[v4+ styles]', '[v4 styles]'))
                    fields = []
                    continue
                if in_styles and line.lower().startswith('format:'):
                    fields = [f.strip().lower() for f in line.split(':', 1)[1].split(',')]
                elif in_styles and line.lower().startswith('style:'):
                    values = line.split(':', 1)[1].split(',')
                    idx = fields.index('fontname') if 'fontname' in fields else 1
                    if idx < len(values):
                        families.add(normalize_family(values[idx]))
                elif line.lower().startswith('dialogue:'):
                    for match in _FN_TAG_RE.findall(line):
                        families.add(normalize_family(match))
    except OSError as e:
        logger.warning('cannot read subtitle file "%s": %s', path, e)
        return set()

    return families - _IGNORED_FAMILIES


def resolve(required: Set[str], present: Set[str],
            index: Dict[str, List[str]]) -> Tuple[List[str], List[str]]:
    """Split *required* families into font files to attach and unresolved names.

    Args:
        required: Families referenced by the subtitle scripts.
        present: Families already available in the container's attachments.
        index: Font library index from :func:`build_index`.

    Returns:
        ``(paths, missing)`` — font files to attach, and families found neither
        in the attachments nor in the library.
    """
    paths: List[str] = []
    missing: List[str] = []
    for family in sorted(required):
        if family in present:
            continue
        found = index.get(family)
        if found:
            for path in found:
                if path not in paths:
                    paths.append(path)
        else:
            missing.append(family)
    return paths, missing
