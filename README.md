# TinySSG

## Overview

TinySSG is a simple static site generator with file-based routing.
It combines simplicity and flexibility by writing pages in Python code with a simple structure.

## Install

```bash
pip install tinyssg
````

## Usage

### directory structure

Configure the directory as follows.The directory name can be changed with an optional argument.

```text
  |-- pages         Place Python files for SSG deployment.
  |-- libs          Place Python files that are not SSG target files (e.g. libraries).
  |-- static        Place static files that are not subject to SSG (css, images, etc.)
  |-- dist          This is the directory where SSG results will be output.The contents of this directory can be published as a web site by placing it on a web server.
        |-- static  The static directory is copied to this directory.
````

### Creating pages

Create a Python file in the `pages` directory and create a class that extends the `TinySSGPage` class.

```python
from tinyssg import TinySSGPage

class IndexPage(TinySSGPage):.
    def query(self):.
        return {
            'title': 'Index', 'content': 'Hello, World!
            'content': 'Hello, World!'
        }

    def template(self): return
        return '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{{ title }}</title>
</head>
<body>
  <h1>{{ title }}</h1>
  <p>{{ content }}</p>
</body>
</html>'''
```

Building it will generate an HTML file with the same name as the Python file.
If multiple `TinySSGPage` inherited classes are defined in the Python file, the Python file name becomes the folder name and the class name in it becomes the HTML file name.

The `query` method returns the data to be passed to the template, and the `template` method returns the HTML template.
TinySSG uses the return values of these methods to generate HTML.

The data returned by the `query` method must be in Python dictionary format or Python dictionary list format.
In the case of dictionary format, an HTML file is generated with the python filename or class name, and in the case of list format, a directory is created equal to the python filename or class name, and by default, an HTML file is generated with a filename of .html, a number from 1.
If a string representing a key name is returned with the list as a tuple on `return`, an HTML file is generated with the value corresponding to the key as the file name.

By default, `TinySSG` simply replaces the parts of the template enclosed in `{{ key name }}` with the value corresponding to the key in the dictionary that is the return value of the `query` method,
You can also override the `render` method for more complex processing, or use a template engine such as Jinja2.

You can also define a process to convert the rendered text to final HTML by overriding the `translate` method.
If you use the markdown library here to describe the process of conversion, you can write the template in Markdown instead of HTML.

Each page must be defined individually, but since this is a simple Python class, if you want to apply it to multiple pages, you can create a class that defines the common parts and inherit it to easily apply it without copying any code.

### Start local server for development.

```bash
python -m tinyssg dev
```

The local server for development will be started.You can see the generated HTML by accessing ``http://localhost:8000``.

If you change files in the `pages`, `libs`, or `static` directories, the server will automatically restart to reflect the changes.

### Generating HTML

```bash
python -m tinyssg gen
```

HTML files will be generated in the `dist` directory.

### options (excerpt)

```text

usage: python -m tinyssg [--page PAGE] [--static STATIC] [--lib LIB] [--input INPUT] [--output OUTPUT] [--port PORT] [--wait WAIT] [--nolog] [--noreloadnoreload] [--noopen] [--curdir CURDIR] [mode]

MODE:

  Specifies startup mode (gen = generate HTML files, dev = start local server for development).

Options:
  --page PAGE, -p PAGE        Directory for page files
  --static STATIC, -s STATIC  Directory for static files
  --lib LIB, -l LIB           Directory for library files
  --output OUTPUT, -o OUTPUT  Specify output directory.
  --input INPUT, -i INPUT     Specifies which files to include in SSG (if not specified, all files in the directory are included).
  --port PORT, -P PORT        Specify the port number of the development server.
  --wait WAIT, -w WAIT        Wait time to prevent multiple restarts.
  --nolog, -n                 Do not output request log to development server
  --noreload, -r              Don't restart development server automatically.
  --noopen, -N                Do not open browser when starting development server
  --curdir CURDIR, -C CURDIR  Specify current directory.
```
