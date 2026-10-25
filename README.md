# file-hasher

Консольная утилита для хеширования файлов и каталогов, сравнения файлов и поиска дубликатов.

## Возможности

- SHA-256 и BLAKE3.
- Потоковое чтение файлов блоками по 64 КБ.
- Рекурсивный обход каталогов.
- Обработка ошибок чтения и заблокированных файлов без остановки работы.
- Сравнение двух файлов по хешу.
- Поиск дубликатов.
- JSON-отчёты.

## Установка

Требуется Python 3.8+.

```powershell
pip install -r requirements.txt
```

## Использование

```powershell
python hasher.py hash -p file.bin -a sha256
python hasher.py hash -p "C:\data" -a blake3 -o report.json --verbose
python hasher.py compare --path first.bin second.bin
python hasher.py compare -p1 first.bin -p2 second.bin
python hasher.py find-duplicates -p "C:\data" -a sha256 -o duplicates.json
python hasher.py report -p "C:\data"
```

Команда `report` без `-o` сохраняет отчёт в `hasher_report.json` в текущем каталоге.

Коды возврата:

- `0` — успех;
- `1` — критическая ошибка или неверные аргументы.

## Структура

```text
hasher.py           точка входа
hasher_app/core.py  хеширование, обход файлов и поиск дубликатов
hasher_app/report.py JSON и консольный вывод
hasher_app/cli.py   аргументы командной строки
```
