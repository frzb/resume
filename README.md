# My resume generator ![Build and Deploy](https://github.com/frzb/resume/actions/workflows/build_and_deploy.yml/badge.svg)
This is my custom resume generator. It creates a static website and/or a PDF document.

## Why?
Why I am not using an already existing static site generator like Jekyll or Hugo?  
I wanted to get more familiar with one of my weak spots - web development: HTML, CSS and templating with Jinja.

## Features

* Input data as [JSON resume](https://jsonresume.org/schema)
* Exclude/include private data
* Python 3.10
* Responsive design for mobile devices
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

### Input data

Input resume data is placed in `input/resume.json`.  
Private resume data can be placed in  `input/private/private_resume.json`.

### Example

```
$  poetry run python3 main.py --include-private-data
```
