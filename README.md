# Analog Clock App (Python-only)

This project is an analog clock web app implemented 100% in Python.

## Requirements (Windows)

- Python 3.10+

## Run (Windows PowerShell)

1) Install

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

2) Start the web UI

```bash
python -m analog_clock_app.main
```

Open `http://localhost:8080/`.

## Tests

### Pytest

```bash
python -m pip install -e ".[dev]"
pytest
```

### Unittest

```bash
$env:PYTHONPATH="src"
python -m unittest discover -s tests -p "test_*.py"
```

## Static typing

```bash
python -m pip install -e ".[dev]"
mypy
```

## Notes

- The clock is rendered as SVG (no digital clock display).
- Settings and presets are persisted in SQLite at `./data/app.db` by default.
- You can override the database path with `ANALOG_CLOCK_DB`.
