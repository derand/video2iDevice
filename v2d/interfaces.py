# -*- coding: utf-8 -*-
"""Abstract base classes (interfaces) for Video2iDevice components.

These ABCs define the public contracts for encoders, packagers, and converters.
Concrete implementations live in the mixin classes under v2d/ and v2d/encoding/.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseRunner(ABC):
    """Interface for ffmpeg command execution."""

    @abstractmethod
    def execute_ffmpeg_command(
        self, params: List[str], percentagePrefix: Optional[str] = None
    ) -> Tuple:
        """Execute an ffmpeg command, streaming its output.

        Args:
            params: ffmpeg argument list (without the executable itself).
            percentagePrefix: Optional label shown in the progress line.

        Returns:
            A tuple ``(retcode, libx264_log, libx264_log_settings)``.

        Raises:
            FfmpegError: if ffmpeg exits with a non-zero return code.
        """


class BaseVideoEncoder(ABC):
    """Interface for video stream encoding."""

    @abstractmethod
    def cVideo(self, iFile: str, stream: Any, oFile: str) -> None:
        """Encode or copy a video stream to *oFile*.

        Args:
            iFile: Path to the source media file.
            stream: A ``cStream`` object describing the video stream.
            oFile: Destination path for the encoded video track.
        """


class BaseAudioEncoder(ABC):
    """Interface for audio stream encoding."""

    @abstractmethod
    def cAudio(self, iFile: str, stream: Any, oFile: str) -> None:
        """Encode or copy an audio stream to *oFile*.

        Args:
            iFile: Path to the source media file.
            stream: A ``cStream`` object describing the audio stream.
            oFile: Destination path for the encoded audio track.
        """


class BaseSubtitleEncoder(ABC):
    """Interface for subtitle stream extraction and conversion."""

    @abstractmethod
    def cSubs(
        self,
        iFile: str,
        stream: Any,
        informer: Any,
        prms: Dict,
        oFile: str,
    ) -> Optional[str]:
        """Convert a subtitle stream to TTXT format in *oFile*.

        Args:
            iFile: Path to the source media file.
            stream: A ``cStream`` object describing the subtitle stream.
            informer: The media informer object used for stream metadata.
            prms: Extra parameters passed to the subtitle converter.
            oFile: Destination path for the converted TTXT subtitle track.

        Returns:
            Path to the output subtitle file, or None to skip.
        """


class BasePackager(ABC):
    """Interface for building the final media container."""

    @abstractmethod
    def createMPEG(self, files: List, fi: Any) -> str:
        """Build the final MP4/M4V container.

        Args:
            files: List of ``(type, path, stream)`` tuples for each track.
            fi: Source file info object used to derive the output filename.

        Returns:
            Path to the finished output file.
        """

    @abstractmethod
    def createMKV(self, files: List, fi: Any) -> str:
        """Build a Matroska (MKV) container.

        Args:
            files: List of ``(type, path, stream)`` tuples for each track.
            fi: Source file info object used to derive the output filename.

        Returns:
            Path to the finished MKV output file.
        """


class BaseConverter(ABC):
    """Interface for the main media conversion workflow."""

    @abstractmethod
    def encodeMedia(self, fi: Any) -> str:
        """Encode all streams of *fi* and assemble the output container.

        Args:
            fi: A media file info object describing the input file.

        Returns:
            Path to the finished output file.
        """

    @abstractmethod
    def fileProcessing(self, fi: Any) -> None:
        """Process a single input file end-to-end.

        Args:
            fi: A media file info object describing the input file.
        """
