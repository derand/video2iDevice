# To-Do List: Video2iDevice Improvements

## Виконано (Completed)
- [x] **Виправити integer division (`/` → `//`)**
    - [x] `mediaInfo.py`: `humanTime()` — рядки 226-231
    - [x] `subConverter.py`: `int2time()`, `__insert()`, `writeOut()`
    - [x] `2iDevice.py`: `time_str` — рядок 1833
    - [x] `snapshots.py`: `tm` обчислення
- [x] **Виправити bytes vs str порівняння**
    - [x] `mpeg4fixer.py`: `'moov'` → `b'moov'` і т.д. (~20+ місць)
    - [x] `mpeg4viewer.py`: аналогічні зміни
    - [x] Додано `.rstrip(b'\x00')` до парсингу імен секцій
    - [x] Додано кодування для track names
- [x] **Замінити deprecated `string` модуль**
    - [x] `2iDevice.py`: `string.find(el, ':')` → `el.find(':')`
    - [x] `subConverter.py`: `string.upper()` → `.upper()`, `string.join()` → `' '.join()`
    - [x] `json_ex.py`: `string.whitespace` → inline константа
    - [x] Видалено `import string` з усіх файлів
- [x] **Виправити json_ex.py**
    - [x] `type(key) is not bytes` → `not isinstance(key, str)`
    - [x] `ty is int or ty is int` → `ty is int` (дубльована умова)
    - [x] Видалено `import types`
- [x] **Замінити `os.system()` на безпечні альтернативи**
    - [x] `mpeg4fixer.py`: `os.system(cmd)` → `shutil.move()`
    - [x] `subConverter.py`: `os.system(cmd)` → `shutil.move()`
- [x] **Замінити `rv[len(rv):]` на `.extend()`**
    - [x] ~15 місць в `2iDevice.py`
    - [x] 1 місце в `snapshots.py`
- [x] **Прибрати `from v2d_utils import *`**
    - [x] `2iDevice.py`: явний імпорт 8 символів
    - [x] `mediaInfo.py`: явний імпорт 5 символів
    - [x] `snapshots.py`: явний імпорт 6 символів
- [x] **Замінити `type(x)==type(y)` на `isinstance()`**
    - [x] 4 місця в `2iDevice.py`

## Priority 1: Critical (Easy Wins - High Impact)
- [x] **Винести XMPP credentials у `.env`**
    - [x] Створено `.env` з реальними credentials (в `.gitignore`)
    - [x] Створено `.env.example` — шаблон для нових розробників
    - [x] `constants.py` читає з `os.environ`, опціонально завантажує `.env` через `python-dotenv`
    - [x] `.env` додано до `.gitignore`
- [x] **Замінити `json_ex.py` на стандартний `json` модуль**
    - [x] `import json_ex` → `import json` в `2iDevice.py`
    - [x] 3x `json_ex.JsonReader().read(x)` → `json.loads(x)`
    - [x] `json_ex.write(x)` → `json.dumps(x)`
    - [x] `json_ex.py` видалено
- [x] **Використовувати `with` для файлових операцій**
    - [x] `mpeg4fixer.py`: `fixFlagsAndSubs()`, `__getFileStruct()`, `setTrackNames()`
    - [x] `mpeg4viewer.py`: top-level `f = open(fn, 'rb')`
    - [x] `subConverter.py`: `writeOut2srt()`, `writeOut2srt2()`, `writeOut2ttxt()`, `readAss()`, `readSrt()`, `readAssStyles()`
    - [x] `fileCoding.py`: `open(filename, 'rb').read()` → `with open(...) as f:`
    - [x] `2iDevice.py`: `correct_profile()` try/finally → `with`

## Priority 2: High (Structural Improvements)
- [x] **Замінити глобальний STTNGS на dataclass**
    - [x] Створено `ConversionSettings` dataclass з ~80 типізованих полів
    - [x] Статичні поля з дефолтами, Optional поля (None = не задано)
    - [x] Включено всі AtomicParsley/iTunes metadata поля
    - [x] Backward-compatible: `__getitem__`, `__setitem__`, `__contains__`, `get()`
    - [x] `STTNGS = ConversionSettings(version=__version__)` — весь існуючий код працює
    - [x] Додано `import struct` (був відсутній, але використовувався в `correct_profile()`)
- [x] **Переписати CLI парсинг з argparse**
    - [x] `snapshots.py`: замінено ручний парсинг на `argparse` (з `--help`, валідацією типів)
    - [ ] `2iDevice.py`: пропущено — існуючі launch templates залежать від поточного формату аргументів
- [x] **Розбити великі методи**
    - [x] `getSettings()` скорочено з ~147 до ~18 рядків
    - [x] Витягнуто `_apply_flag(ckey) → (saveP, waitParam)` (~50 рядків)
    - [x] Витягнуто `_apply_value(ckey, el)` (~70 рядків)
- [x] **Перейменувати методи для читабельності**
    - [x] `iTagger()` → `tag_file()`
    - [x] `__exeFfmpegCmd()` → `execute_ffmpeg_command()`
    - [x] `loadSettingsFile()` → `load_configuration_from_file()`

## Priority 3: Medium (Code Quality)
- [x] **Використати Enum для типів потоків**
    - [x] Створено `StreamType(IntEnum)` в `mediaInfo.py` (VIDEO=0, AUDIO=1, SUBTITLE=2, IMAGE=3)
    - [x] Замінено всі магічні числа у `mediaInfo.py` та `2iDevice.py`
    - [ ] Винести інші магічні константи (bitrates, frame rates, extensions)
- [ ] **Додати logging замість print()** _(відкладено)_
    - [ ] Замінити `print()` на `logging` module calls
    - [ ] Налаштувати рівні логування (INFO, DEBUG, ERROR)
- [x] **Покращити обробку помилок**
    - [x] Видалено bare `except:` clauses (4 місця: 2iDevice.py×2, subConverter.py, v2d_utils.py)
    - [x] Замінено на `(OSError, UnicodeDecodeError)`, `ValueError`, `Exception`
- [x] **Видалити закоментований/мертвий код**
    - [x] Прибрано закоментовані блоки з усіх файлів (~130+ рядків мертвого коду)
- [x] **Додати docstrings**
    - [x] Module docstrings до всіх файлів
    - [x] Class docstrings (`Video2iDevice`, `LogToFile`, `MediaInformer`, `cStream`, `cMediaInfo`, `cChapter`, `subConverter`, `mpeg4fixer`)
    - [x] Method docstrings (Google-style) до всіх публічних методів
- [ ] **Перейменувати криптичні змінні** _(відкладено)_
    - [ ] `tmp` → контекстно-відповідні імена
    - [ ] `el` → `argument`, `ckey` → `current_key`, `prm` → `parameter`, `rv` → `result`
- [x] **Додати Type Hints**
    - [x] Python 3 type hints до сигнатур усіх методів у всіх файлах
- [x] **Валідація вхідних даних**
    - [x] `_apply_value()`: валідація bitrates (`ab`, `vb` > 0), resolution (`s`), frame rate (`vr`, `r` > 0)

## Priority 4: Structural (Long-term)
- [x] **Модуляризувати кодову базу**
    - [x] Розбити `mediaInfo.py` на пакет `media/` (types.py, informer.py)
    - [x] Розбити `2iDevice.py` на пакет `v2d/` (settings, log, cli, runner, tagging, encoding/*, packaging, converter)
    - [x] `2iDevice.py` стала тонким entry point
    - [x] Створити пакетну структуру (`core`=`v2d/`, `media/`, `encoding`=`v2d/encoding/`, `subtitles/`, `utils/`)
        - [x] `utils/__init__.py` — re-exports з v2d_utils, fileCoding, mpeg4fixer
        - [x] `subtitles/__init__.py` — re-exports subConverter
- [x] **Абстрактні інтерфейси**
    - [x] `v2d/interfaces.py`: BaseRunner, BaseVideoEncoder, BaseAudioEncoder, BaseSubtitleEncoder, BasePackager, BaseConverter
    - [x] Міксіни успадковуються від відповідних ABC: RunnerMixin, VideoEncoderMixin, AudioEncoderMixin, SubtitleEncoderMixin, PackagingMixin, Video2iDevice

## Priority 5: Testing
- [ ] **Додати юніт-тести**
    - [ ] Налаштувати testing framework (`pytest`)
    - [ ] Тести для парсингу конфігурації
    - [ ] Тести для utility функцій
    - [ ] Фікстури для зразків медіа-файлів
