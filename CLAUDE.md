# video2iDevice — CLAUDE.md

## Overview

CLI tool for converting video files into a format suitable for playback on iOS/Android
devices. Primary target platform: Raspberry Pi (h264_v4l2m2m).

Usage: `python3 2iDevice.py [options] FILE [FILE ...]`

## Architecture

The main class `Video2iDevice` (`v2d/converter.py`) is assembled via multiple inheritance
from mixins:

```
Video2iDevice
  ├── BaseConverter          (v2d/interfaces.py)
  ├── CLIParserMixin         (v2d/cli.py)        — argparse, parses argv → STTNGS
  ├── RunnerMixin            (v2d/runner.py)      — _exeCmd, execute_ffmpeg_command
  ├── TaggingMixin           (v2d/tagging.py)     — AtomicParsley, buildFN, getLang
  ├── VideoEncoderMixin      (v2d/encoding/video.py)     — cVideo, _prepareHardsubFile
  ├── AudioEncoderMixin      (v2d/encoding/audio.py)     — cAudio
  ├── SubtitleEncoderMixin   (v2d/encoding/subtitles.py) — cSubs, _streamFromFAdd
  └── PackagingMixin         (v2d/packaging.py)   — createMPEG, createMKV
```

Data flow:
1. `CLIParserMixin.getSettings(argv)` → populates the global `STTNGS`
2. `splitMedia()` → iterates over files, builds `fi` (fileInfo)
3. `encodeMedia(fi)` → encodes video/audio/subtitles, collects temp file list
4. `createMPEG()` / `createMKV()` → packages into the final container

## Key Files

| File | Role |
|------|------|
| `2iDevice.py` | entry point |
| `v2d/settings.py` | `STTNGS: ConversionSettings`, `StreamSpec` dataclass, `__version__` |
| `v2d/cli.py` | argparse parser; custom Action classes for order-dependent `-vfile/-afile/-sfile` |
| `v2d/converter.py` | `Video2iDevice`, `encodeMedia`, `fileProcessing` |
| `v2d/encoding/video.py` | `cVideo`, `_prepareHardsubFile` |
| `v2d/encoding/subtitles.py` | `cSubs`, `_streamFromFAdd` |
| `media/informer.py` | `MediaInformer` — parses ffmpeg+mediainfo+mkvinfo → `cMediaInfo` |
| `media/types.py` | `cStream`, `cMediaInfo`, `StreamType`, `cStream.format()` |
| `v2d_utils.py` | paths to external tools (ffmpeg, MP4Box, mkvtoolnix, mediainfo) |
| `v2d/exceptions.py` | `FfmpegError` |

## Key Data Structures

**`STTNGS: ConversionSettings`** — global singleton, dict-compatible via `__getitem__`.

**`StreamSpec`** (`v2d/settings.py`) — describes one external stream added via `-vfile/-afile/-sfile`:
```python
StreamSpec(stream_type=2, path='file.mkv', stream='4', hardsub=True)
```
`fadd.as_extended_dict()` → dict for `stream.params['extended']` (backward compat).

**`cStream`** (`media/types.py`) — a single stream within a file. Key method:
- `format()` → returns a format string: `'h264'`, `'aac'`, `'ass'`, `'srt'`, etc.
  For subtitles, reads `Codec_ID` (`S_TEXT/ASS` → `'ass'`, `S_TEXT/UTF8` → `'srt'`).

**`cMediaInfo`** — container for all streams in a file. Populated by `MediaInformer`
from three sources: ffmpeg + mediainfo + mkvinfo (for MKV files).

## CLI — Order-Dependent Parameters

`-vfile/-afile/-sfile` start a new `StreamSpec` in `STTNGS.fadd`.
Subsequent flags (`-hardsub`, `-copy`, `-stream`, `-sname`, `-delay`, ...) apply to the
**last** added StreamSpec:

```
-sfile video.mkv -stream 4 -hardsub
                 └─────────────────── applies to video.mkv
```

## Platforms

| | macOS (dev) | Raspberry Pi (prod) |
|--|-------------|---------------------|
| ffmpeg | `binary/ffmpeg` | system `ffmpeg` |
| vcodec | `libx264` | `h264_v4l2m2m` |
| tools | `binary/` | system (`apt`) |

On RPi, always pass `-vcodec h264_v4l2m2m`.

## Typical Commands

```bash
# Convert with hardsub (ASS from MKV, track 4)
python3 2iDevice.py -sfile [NAME].mkv -stream 4 -hardsub \
  -streams v:a_jpn -s *x720 -b 4500 -ab 160 -ar 48000 \
  -vcodec h264_v4l2m2m video.mkv

# File info
python3 2iDevice.py -info video.mkv

# Short stream listing
python3 2iDevice.py -info short video.mkv
```

## Deploy to RPi

```bash
make deploy-dry   # preview what will be synced
make deploy       # rsync → rpi42:src/video2iDevice_v2/
```
