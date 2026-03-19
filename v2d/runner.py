# -*- coding: utf-8 -*-
"""ffmpeg/command runner mixin for Video2iDevice."""

import sys
import re
from subprocess import Popen, PIPE, STDOUT
from typing import Optional, List

from v2d.settings import STTNGS
from v2d_utils import ffmpeg_path, add_separator_to_filepath


class RunnerMixin:
    """Mixin providing ffmpeg execution and subprocess helpers."""

    def _printCmd(self, cmd: str) -> None:
        """Print *cmd* in green and write to log."""
        print(': \033[1;32m%s\033[00m' % cmd)
        self.log.put('\n: \033[1;32m%s\033[00m\n' % cmd, True)

    def execute_ffmpeg_command(self, params: List[str], percentagePrefix: Optional[str] = None) -> tuple:
        """Run an ffmpeg command and stream its output to stdout.

        Args:
            params: ffmpeg arguments (without the ffmpeg binary itself).
            percentagePrefix: Optional string shown at the start of each
                progress output line (e.g. a stream label).

        Returns:
            A 3-tuple ``(retcode, libx264_log, libx264_log_settings)``.
        """
        def timeToMs(hoursMinsSecMs_array):
            hours = int(hoursMinsSecMs_array[0])
            mins = int(hoursMinsSecMs_array[1])
            secs = int(hoursMinsSecMs_array[2])
            ms = int(hoursMinsSecMs_array[3])
            return ((hours * 60 + mins) * 60 + secs) * 100 + ms

        cmd = [ffmpeg_path, ]
        for prm in params:
            if prm[0] == '"' and prm[-1] == '"':
                cmd.append(prm[1:-1])
            else:
                cmd.append(prm)
        cmd_str = add_separator_to_filepath(cmd[0])
        for i in range(1, len(cmd)):
            if cmd[i].find(' ') == -1:
                cmd_str += ' %s' % cmd[i]
            else:
                cmd_str += ' "%s"' % cmd[i]
        self._printCmd(cmd_str)
        if STTNGS.get('test_mode'):
            return (0, None, None)
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        retcode = 0
        line = ''
        duration = None
        duration_re_compiled = re.compile(r'Duration:\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})')
        time = 0
        time_re_compiled = re.compile(r'.*time=\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})')
        libx264_log_settings = []
        libx264_log = []

        tmp_process_catched = False
        tmp_line = None
        while True:
            retcode = p.poll()
            try:
                ch = p.stdout.read(1).decode("utf-8")
            except UnicodeDecodeError as e:
                ch = ''
            if ch == '\r' or ch == '\n':
                line = line.strip()
                process_catched = False
                if duration is None:
                    duration_re = duration_re_compiled.search(line)
                    if duration_re:
                        duration = float(timeToMs(duration_re.groups()))
                else:
                    time_re = time_re_compiled.search(line)
                    process_catched = time_re != None
                    if time_re:
                        time = timeToMs(time_re.groups()[0:4])
                        try:
                            if time > duration:
                                time = duration
                        except Exception as e:
                            p.kill()
                            raise e
                    if line[:len('[libx264')] == '[libx264':
                        if time == 0:
                            libx264_log_settings.append(line)
                        else:
                            libx264_log.append(line)
                s = ''
                if STTNGS['vv']:
                    s = line
                else:
                    if process_catched:
                        if percentagePrefix is not None:
                            s = percentagePrefix
                        s += '  %.2f%% %s   ' % (float(time) * 100.0 / float(duration), line)
                    elif tmp_process_catched:
                        if percentagePrefix is not None:
                            s = percentagePrefix
                        s += '  %.2f%% %s   ' % (float(duration) * 100.0 / float(duration), tmp_line)
                if len(s):
                    sys.stdout.write(s + ch)
                    sys.stdout.flush()
                if ch == '\n':
                    if tmp_line is not None and tmp_line[-1] == '\r':
                        self.log.put(tmp_line, False)
                    self.log.put(line + ch, True)
                tmp_process_catched = process_catched
                tmp_line = line + ch
                line = ''
            else:
                line += ch
            if retcode is not None and not STTNGS['vv']:
                print()
                for l in libx264_log_settings:
                    print(l)
                if len(libx264_log_settings) > 0 and len(libx264_log):
                    print('--- h264 log ---')
                for l in libx264_log:
                    print(l)
                break
        if retcode != 0:
            print(cmd)
            sys.exit()
        return (retcode, libx264_log, libx264_log_settings)

    def _exeCmd(self, cmd: List[str], check_exit_code: bool = True) -> int:
        """Run an arbitrary command, streaming output to stdout.

        Args:
            cmd: Command + arguments list.
            check_exit_code: If True, call sys.exit on non-zero exit code.

        Returns:
            Process exit code.
        """
        cmd_str = add_separator_to_filepath(cmd[0])
        print(cmd)
        for i in range(1, len(cmd)):
            if cmd[i].find(' ') == -1:
                cmd_str += ' %s' % cmd[i]
            else:
                cmd_str += ' "%s"' % cmd[i]
        self._printCmd(cmd_str)
        if STTNGS.get('test_mode'):
            return 0
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        line = ''
        tmp_line = None
        retcode = 0
        while True:
            retcode = p.poll()
            try:
                ch = p.stdout.read(1).decode("utf-8")
            except UnicodeDecodeError as e:
                ch = ''
            if ch == '\r' or ch == '\n':
                sys.stdout.write(line + ch)
                if ch == '\n':
                    if tmp_line is not None and tmp_line[-1] == '\r':
                        self.log.put(tmp_line, False)
                    self.log.put(line + ch, True)
                tmp_line = line + ch
                line = ''
            else:
                line += ch
            if retcode is not None and len(ch) == 0:
                break
        if check_exit_code and retcode != 0:
            print(cmd)
            print('Exit code: %d' % retcode)
            sys.exit()
        return retcode
