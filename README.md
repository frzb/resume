# My resume generator

This is my custom slight  resume generator. It creates a static website and/or a PDF document.

## Features

* Input data as [JSON resume](https://jsonresume.org/schema
* Exclude/include private data
* Python 3.10
* [Jinja](https://jinja.palletsprojects.com/en/stable/) for HTML templating
* [pyTailwindCSS](https://pypi.org/project/pytailwindcss/) standalone Tailwind CSS in Python without Node.js 
* [WeasyPrint](https://weasyprint.org/) for PDF document creation
* Automatic creation of output files in case of changes during development by [Watchdog](https://pypi.org/project/watchdog/)
* [Poetry](https://pypi.org/project/watchdog/) for dependency management

## Setup

### 1. [Install Poetry](https://python-poetry.org/docs/#installation)
```
$ curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install dependencies
```
$ poetry install
```

## Usage

```
Usage: main.py [OPTIONS] COMMAND [ARGS]...

  Watch for file changes, trigger automatic build

Options:
  --include-private-data  Include private data
  --help                  Show this message and exit.

Commands:
  one-shot  Build CSS file and render Jinja template one time and exit
```

### Example

```
$  poetry execute python3 main.py --include-private-data
```
