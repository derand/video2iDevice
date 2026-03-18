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
- [ ] **Замінити глобальний STTNGS на dataclass**
    - [ ] Створити `ConversionSettings` dataclass
    - [ ] Передавати settings явно замість глобальних змінних
- [ ] **Переписати CLI парсинг з argparse**
    - [ ] `2iDevice.py`: замінити ручний парсинг `sys.argv` на `argparse`
    - [ ] `snapshots.py`: аналогічно
- [ ] **Розбити великі методи**
    - [ ] Рефакторити `getSettings()` в `2iDevice.py` (200+ рядків)
    - [ ] Винести логіку парсингу параметрів у хелпер-методи
- [ ] **Перейменувати методи для читабельності**
    - [ ] `iTagger()` → `tag_file()`
    - [ ] `__exeFfmpegCmd()` → `execute_ffmpeg_command()`
    - [ ] `loadSettingsFile()` → `load_configuration_from_file()`

## Priority 3: Medium (Code Quality)
- [ ] **Використати Enum для типів потоків**
    - [ ] Створити `StreamType` enum замість магічних чисел (0=video, 1=audio, 2=subtitle)
    - [ ] Винести інші магічні константи (bitrates, frame rates, extensions)
- [ ] **Додати logging замість print()**
    - [ ] Замінити `print()` на `logging` module calls
    - [ ] Налаштувати рівні логування (INFO, DEBUG, ERROR)
- [ ] **Покращити обробку помилок**
    - [ ] Видалити bare `except:` clauses
    - [ ] Ловити конкретні виключення (`FileNotFoundError`, `ValueError`)
- [ ] **Видалити закоментований/мертвий код**
    - [ ] Прибрати закоментовані блоки коду у всіх файлах
- [ ] **Додати docstrings**
    - [ ] Module docstrings до всіх файлів
    - [ ] Class docstrings (`Video2iDevice`, `LogToFile`, `MediaInformer`)
    - [ ] Method docstrings з описом аргументів і return values
- [ ] **Перейменувати криптичні змінні**
    - [ ] `tmp` → контекстно-відповідні імена
    - [ ] `el` → `argument`, `ckey` → `current_key`, `prm` → `parameter`, `rv` → `result`
- [ ] **Додати Type Hints**
    - [ ] Python 3 type hints до сигнатур методів
- [ ] **Валідація вхідних даних**
    - [ ] Валідувати аргументи CLI (позитивні bitrates, коректні роздільні здатності)

## Priority 4: Structural (Long-term)
- [ ] **Модуляризувати кодову базу**
    - [ ] Розбити `2iDevice.py` і `mediaInfo.py` на менші модулі
    - [ ] Створити пакетну структуру (`core`, `media`, `encoding`, `subtitles`, `utils`)
- [ ] **Абстрактні інтерфейси**
    - [ ] Створити базові класи для media converters

## Priority 5: Testing
- [ ] **Додати юніт-тести**
    - [ ] Налаштувати testing framework (`pytest`)
    - [ ] Тести для парсингу конфігурації
    - [ ] Тести для utility функцій
    - [ ] Фікстури для зразків медіа-файлів
