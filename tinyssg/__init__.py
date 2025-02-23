import argparse
import importlib.util
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler


class TinySSGPage:
    """
    Base class for HTML page generation
    """
    def render(self, src: str, data: dict) -> str:
        """
        Template rendering process
        """
        return TinySSGUtility.render_variables(src, data)

    def translate(self, basestr: str) -> str:
        """
        Process to convert rendered text to HTML
        """
        return basestr

    def query(self) -> dict:
        """
        Data Acquisition Process
        """
        return {}

    def template(self) -> str:
        """
        Template string
        """
        raise TinySSGException(f"The Page class corresponding to {self.__class__.__name__} does not appear to be implemented correctly.")

    def indent(self, src: str, indent: int = 0) -> str:
        """
        Indentation process
        """
        return TinySSGUtility.set_indent(src, indent)


class TinySSGException(Exception):
    """
    TinySSG Exception Class
    """
    pass


class TinySSGUtility:
    """
    TinySSG Utility Class
    """
    @classmethod
    def render_variables(cls, src: str, data: dict, start_delimiter: str = r'\{\{\s?', end_delimiter: str = r'\s?\}\}') -> str:
        """
        Replace variables in the template with the values in the dictionary
        """
        result = src
        for key, value in data.items():
            result = re.sub(start_delimiter + re.escape(key) + end_delimiter, str(value), result)
        return result

    @classmethod
    def set_indent(cls, src: str, indent: int = 0) -> str:
        """
        Set the indent level of the text
        """
        return textwrap.indent(textwrap.dedent(src).strip(), (' ' * indent)) + '\n'

    @classmethod
    def merge_dict(cls, base: dict, add: dict, overwrite: bool = True, extend: bool = True, reverse: bool = False) -> dict:
        """
        Merge dictionaries
        """
        if not isinstance(base, dict) or not isinstance(add, dict):
            raise ValueError('Both base and add must be dictionary type.')

        result = base.copy()

        for key, value in add.items():
            TinySSGUtility.merge_dict_value(result, key, value, overwrite, extend, reverse)

        return result

    @classmethod
    def extend_list(cls, base: any, add: any) -> list:
        """
        List Expansion
        """
        if base is None:
            return add if isinstance(add, list) else [add]

        result = base.copy() if isinstance(base, list) else [base]

        if isinstance(add, list):
            result.extend(add)
        else:
            result.append(add)

        return result

    @classmethod
    def merge_dict_value(cls, base: any, key: str, value: any, overwrite: bool = True, extend: bool = True, reverse: bool = False) -> None:
        """
        Merge dictionary values (type-based merging process)
        """
        if not isinstance(base, dict):
            raise ValueError('Base must be dictionary type.')

        if key not in base:
            base[key] = value
        elif isinstance(base[key], dict) and isinstance(value, dict):
            base[key] = TinySSGUtility.merge_dict(base[key], value, overwrite, extend, reverse)
        elif extend and (isinstance(base[key], list) or isinstance(value, list)):
            if reverse:
                base[key] = TinySSGUtility.extend_list(value, base[key])
            else:
                base[key] = TinySSGUtility.extend_list(base[key], value)
        elif overwrite:
            base[key] = value

    @classmethod
    def filter_json_serializable(cls, data):
        """
        Filter only JSON-able objects
        """
        if isinstance(data, (dict, list, str, int, float, bool, type(None))):
            if isinstance(data, dict):
                return {k: TinySSGUtility.filter_json_serializable(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [TinySSGUtility.filter_json_serializable(v) for v in data]
            else:
                return data
        return None

    @classmethod
    def get_serialize_json(cls, data: dict, jsonindent: any = 4) -> str:
        """
        Only JSON-able objects from the dictionary are converted to JSON.
        """
        if not isinstance(data, dict):
            raise ValueError('The specified variable is not a dictionary type.')
        return json.dumps(TinySSGUtility.filter_json_serializable(data), indent=jsonindent)

    @classmethod
    def exclude_double_underscore(cls, data: dict) -> dict:
        """
        Exclude keys beginning with __
        """
        return {k: v for k, v in data.items() if not k.startswith('__')}

    @classmethod
    def get_fullpath(cls, args: dict, pathkey: str = '') -> str:
        """
        Get the full path from the relative path
        """
        if isinstance(args['curdir'], str) and len(args['curdir']) > 0:
            basedir = args['curdir']
        else:
            basedir = os.getcwd()

        if isinstance(args[pathkey], str) and len(args[pathkey]) > 0:
            result = os.path.join(basedir, args[pathkey])
        else:
            result = basedir

        return result

    @classmethod
    def clear_output(cls, output_full_path: str) -> None:
        """
        Delete the output directory
        """
        if os.path.exists(output_full_path):
            shutil.rmtree(output_full_path)

    @classmethod
    def clear_start(cls, args: dict) -> None:
        """
        Delete the output directory
        """
        output_full_path = cls.get_fullpath(args, 'output')
        cls.clear_output(output_full_path)

    @classmethod
    def log_print(cls, message: str) -> None:
        """
        Output log message (Console Execution Only)
        """
        try:
            from IPython import get_ipython  # type: ignore
            env = get_ipython().__class__.__name__
            if env == 'ZMQInteractiveShell':
                return
        except:  # noqa: E722
            pass

        print(message)

    @classmethod
    def error_print(cls, message: str) -> None:
        """
        Output error message
        """
        print(message)


class TinySSGGenerator:
    """
    Generator
    """
    @classmethod
    def check_duplicate_name(cls, files: list, dirs: list) -> list:
        """
        Check for duplicate names in files and directories
        """
        filenames = {os.path.splitext(f)[0] for f in files}
        dirnames = set(dirs)

        conflicts = list(filenames & dirnames)

        return conflicts

    @classmethod
    def extract_page_classes(cls, root: str, filename: str) -> list:
        """
        Extract page classes from the specified file.
        """
        page_classes = []
        check_base_name = TinySSGPage.__name__

        if filename.endswith('.py') and filename != '__init__.py':
            module_name = os.path.splitext(filename)[0]  # Excluding extensions
            module_path = os.path.join(root, filename)

            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for _, members in inspect.getmembers(module):
                    if inspect.isclass(members) and members.__module__ == module_name:
                        parents = [m.__name__ for m in members.__mro__]
                        if check_base_name in parents:
                            page_classes.append(members)

        return page_classes, module_name, module_path

    @classmethod
    def check_input_file(cls, relative_path: str, filename: str, input_file: str) -> bool:
        """
        Check if the input file is the same as the file being processed
        """
        convert_filename = os.path.join(relative_path, os.path.splitext(filename)[0]).replace(os.sep, '/')
        convert_input_file = os.path.splitext(re.sub(r'^\./', '', input_file))[0].replace(os.sep, '/')

        return convert_filename == convert_input_file

    @classmethod
    def search_route(cls, args: dict) -> dict:
        """
        Search for Page classes in the specified directory
        """
        static_path = args['static']
        input_file = args['input']

        try:
            prev_dont_write_bytecode = sys.dont_write_bytecode
            sys.dont_write_bytecode = True

            routes = {}

            full_pages_path = TinySSGUtility.get_fullpath(args, 'page')
            page_counter = 0

            for root, dirs, files in os.walk(full_pages_path):
                relative_path = os.path.relpath(root, full_pages_path)

                conflicts = cls.check_duplicate_name(files, dirs)
                if len(conflicts) > 0:
                    raise TinySSGException(f"The following names conflict between files and directories: {', '.join(conflicts)} in {relative_path}")

                if relative_path == '.':
                    relative_path = ''

                if relative_path == static_path:
                    raise TinySSGException(f"Static file directory name conflict: {os.path.join(full_pages_path, relative_path)}")

                if relative_path.endswith('__pycache__'):
                    continue

                current_dict = routes

                if relative_path:
                    for part in relative_path.split(os.sep):
                        if part not in current_dict:
                            current_dict[part] = {}
                        current_dict = current_dict[part]

                for filename in files:
                    if len(input_file) > 0 and not cls.check_input_file(relative_path, filename, input_file):
                        continue

                    if relative_path == '' and filename == f"{static_path}.py":
                        raise TinySSGException(f"Static file directory name conflict: {os.path.join(root, filename)}")

                    page_classes, module_name, module_path = cls.extract_page_classes(root, filename)
                    page_counter += len(page_classes)
                    if len(page_classes) > 1:
                        current_dict[module_name] = {c.__name__: c for c in page_classes}
                    elif len(page_classes) == 1:
                        current_dict[module_name] = page_classes[0]
                    else:
                        TinySSGUtility.log_print(f"warning: No Page class found in {module_path}")

            if page_counter == 0:
                raise TinySSGException('No Page classes found.')
        finally:
            sys.dont_write_bytecode = prev_dont_write_bytecode

        return routes

    @classmethod
    def create_content(cls, page: TinySSGPage) -> str:
        """
        Generate HTML content from Page class
        """
        basefetch = page.query()
        fetchdata, slugkey = basefetch if isinstance(basefetch, tuple) else (basefetch, None)
        if isinstance(fetchdata, dict):
            baselist = [fetchdata]
            slugkey = None
            single_page = True
        elif isinstance(fetchdata, list):
            if len(fetchdata) == 0:
                return {}
            baselist = fetchdata
            for i in range(len(baselist)):
                if not isinstance(baselist[i], dict):
                    raise TinySSGException('The query method must return a dictionary or a list of dictionaries.')
            single_page = False
        else:
            raise TinySSGException('The query method must return a dictionary or a list of dictionaries.')

        result = {}

        for i in range(len(baselist)):
            if isinstance(slugkey, str) and slugkey in baselist[i]:
                key = baselist[i][slugkey]
            else:
                key = str(i + 1)
            pagedata = baselist[i]
            pagetemp = page.template()
            basestr = page.render(pagetemp, pagedata).strip() + '\n'
            htmlstr = page.translate(basestr)
            if isinstance(htmlstr, str) and len(htmlstr) > 0:
                result[key] = htmlstr

        return result['1'] if single_page else result

    @classmethod
    def traverse_route(cls, route: dict, dict_path: str = '') -> dict:
        """
        Traverse the route dictionary and generate HTML content
        """
        result = {}

        for key, value in route.items():
            if isinstance(value, dict):
                current_path = f"{dict_path}/{key}"
                result[key] = cls.traverse_route(value, current_path)
            else:
                page = value()
                result[key] = cls.create_content(page)

        return result

    @classmethod
    def generate_routes(cls, args: dict) -> dict:
        """
        Generate HTML content dictionary from Page classes
        """
        route = cls.search_route(args)
        return cls.traverse_route(route)

    @classmethod
    def output_file(cls, data: dict, full_path: str) -> None:
        """
        Output the HTML content dictionary to the file
        """
        for key, value in data.items():
            if isinstance(value, dict) and len(value) > 0:
                relative_path = os.path.join(full_path, key)
                if not os.path.exists(relative_path):
                    os.makedirs(relative_path)
                cls.output_file(value, relative_path)
            elif isinstance(value, str):
                with open(os.path.join(full_path, key + '.html'), 'w', encoding='utf-8') as f:
                    f.write(value)

    @classmethod
    def generator_start(cls, args: dict) -> None:
        """
        Generate HTML files from Page classes
        """
        input_full_path = TinySSGUtility.get_fullpath(args, 'page')

        if not os.path.isdir(input_full_path):
            raise TinySSGException(f"The specified page directory does not exist. ({input_full_path})")

        page_data = cls.generate_routes(args)
        output_full_path = TinySSGUtility.get_fullpath(args, 'output')

        if not os.path.exists(output_full_path):
            os.makedirs(output_full_path)

        cls.output_file(page_data, output_full_path)

        static_full_path = TinySSGUtility.get_fullpath(args, 'static')
        output_static_full_path = os.path.join(output_full_path, args['static'])

        if os.path.isdir(static_full_path):
            if not os.path.exists(output_static_full_path):
                os.makedirs(output_static_full_path)
            shutil.copytree(static_full_path, output_static_full_path, dirs_exist_ok=True)


class TinySSGDebugHTTPServer(HTTPServer):
    """
    Custom HTTP server class
    """
    def __init__(self, server_address: tuple, RequestHandlerClass: any, args: dict, route: dict, reload: bool) -> None:
        super().__init__(server_address, RequestHandlerClass)
        self.args = args
        self.route = route
        self.reload = reload


class TinySSGDebugHTTPHandler(SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler
    """
    def __init__(self, *args, **kwargs) -> None:
        try:
            super().__init__(*args, **kwargs)
        except ConnectionResetError:
            pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        return super().end_headers()

    def log_message(self, format: str, *args: any) -> None:
        TinySSGDebug.print_httpd_log_message(self, self.server, format, *args)

    def do_GET(self) -> None:
        TinySSGDebug.httpd_get_handler(self, self.server)


class TinySSGDebug:
    """
    Debug Server
    """
    @classmethod
    def watchdog_script(cls) -> str:
        """
        JavaScript code that checks for file updates from a web browser and reloads the file if there are any updates
        """
        return '''
    <script type="module">
        let __reload_check = () => {
            fetch('/change').then(response => response.json()).then(data => {
                if (data.reload) {
                    console.log('Change detected. Reloading...');
                    location.reload();
                } else {
                    setTimeout(__reload_check, 1000);
                }
            });
        };
        setTimeout(__reload_check, 1000);
    </script>'''

    @classmethod
    def send_ok_response(cls, handler: TinySSGDebugHTTPHandler, content_type: str, content: str = '', add_headers: dict = {}) -> None:
        """
        Send an OK response
        """
        encoded_content = content.encode('utf-8')
        handler.send_response(200)
        handler.send_header('Content-type', content_type)
        handler.send_header('Content-Length', len(encoded_content))
        for key, value in add_headers.items():
            handler.send_header(key, value)
        handler.end_headers()
        handler.wfile.write(encoded_content)

    @classmethod
    def send_no_ok_response(cls, handler: TinySSGDebugHTTPHandler, status: int, content: str = '', add_headers: dict = {}) -> None:
        """
        Send a non-OK response
        """
        handler.send_response(status)
        for key, value in add_headers.items():
            handler.send_header(key, value)
        if isinstance(content, str) and len(content) > 0:
            encoded_content = content.encode('utf-8')
            handler.send_header('Content-type', 'text/plain')
            handler.send_header('Content-Length', len(encoded_content))
            handler.end_headers()
            handler.wfile.write(encoded_content)
        else:
            handler.end_headers()

    @classmethod
    def print_httpd_log_message(cls, handler: TinySSGDebugHTTPHandler, server: TinySSGDebugHTTPServer, format: str, *args: any) -> None:
        """
        Output the log message (HTTPServer)
        """
        if not server.args['nolog'] and not str(args[0]).startswith('GET /change'):
            SimpleHTTPRequestHandler.log_message(handler, format, *args)
            sys.stdout.flush()

    @classmethod
    def httpd_get_handler(cls, handler: TinySSGDebugHTTPHandler, server: TinySSGDebugHTTPServer) -> None:
        """
        Process the GET request
        """
        if handler.path == '/change':
            cls.send_ok_response(handler, 'application/json', json.dumps({'reload': server.reload}))
            server.reload = False
        elif handler.path == '/stop':
            cls.send_ok_response(handler, 'text/plain', 'Server Stopped.')
            server.shutdown()
        elif handler.path.startswith(f"/{server.args['output']}/{server.args['static']}/"):
            redirect_path = re.sub('/' + re.escape(server.args['output']), '', handler.path)
            handler.path = redirect_path
            SimpleHTTPRequestHandler.do_GET(handler)
        elif handler.path == f"/{server.args['output']}":
            cls.send_no_ok_response(handler, 301, '', {'Location': f"/{server.args['output']}/"})
        elif handler.path.startswith(f"/{server.args['output']}/"):
            baselen = len(f"/{server.args['output']}/")
            basename = re.sub(r'\.html$', '', handler.path[baselen:])
            basename = f"{basename}index" if basename.endswith('/') or basename == '' else basename
            output_path = basename.split('/')
            current_route = server.route

            for path in output_path:
                if not isinstance(current_route, dict) or path not in current_route:
                    cls.send_no_ok_response(handler, 404, 'Not Found')
                    return
                current_route = current_route[path]

            if isinstance(current_route, dict):
                cls.send_no_ok_response(handler, 301, '', {'Location': f"{handler.path}/"})
            elif not isinstance(current_route, str):
                TinySSGUtility.error_print(f"Error: The Page class for {handler.path} may not be implemented correctly.")
                cls.send_no_ok_response(handler, 500, 'Internal Server Error')
            else:
                current_route = current_route if server.args['noreload'] else re.sub(r'(\s*</head>)', f"{cls.watchdog_script()}\n\\1", current_route)
                cls.send_ok_response(handler, 'text/html', current_route)
        else:
            cls.send_no_ok_response(handler, 404, 'Not Found')

    @classmethod
    def stop_server(cls, process: any) -> None:
        """
        Stop the debug server
        """
        process.kill()

    @classmethod
    def server_stop_output(cls, process) -> None:
        """
        Output the server stop message
        """
        TinySSGUtility.error_print(f"Server return code:{process.poll()}")
        TinySSGUtility.error_print('Server Output:\n')
        TinySSGUtility.error_print(process.stdout.read() if process.stdout else '')
        TinySSGUtility.error_print(process.stderr.read() if process.stderr else '')

    @classmethod
    def server_start(cls, args: dict) -> None:
        """
        Run the debug server
        """
        reload = args['mode'] == 'servreload'
        route = TinySSGGenerator.generate_routes(args)
        server_address = ('', args['port'])
        httpd = TinySSGDebugHTTPServer(server_address, TinySSGDebugHTTPHandler, args, route, reload)
        TinySSGUtility.error_print(f"Starting server on http://localhost:{args['port']}/{args['output']}/")
        httpd.serve_forever()


class TinySSGLauncher:
    """
    Watchdog and Server Launcher
    """
    @classmethod
    def check_for_changes(cls, mod_time: float, args: dict, pathlits: list) -> bool:
        """
        Check for changes in the specified directories
        """
        path_times = []
        new_mod_time = 0

        try:
            for path in pathlits:
                time_list = [os.path.getmtime(os.path.join(root, file)) for root, _, files in os.walk(path) for file in files]
                if len(time_list) > 0:
                    this_path_time = max(time_list)
                    path_times.append(this_path_time)

            if len(path_times) > 0:
                new_mod_time = max(path_times)

            if new_mod_time > mod_time:
                mod_time = new_mod_time + args['wait']
                return True, mod_time
        except Exception as e:
            TinySSGUtility.log_print(f"update check warning: {e}")

        return False, mod_time

    @classmethod
    def launch_server(cls, args: dict, reload: bool) -> None:
        """
        Launch the server
        """
        servcommand = 'serv' if not reload else 'servreload'

        newargv = args.copy()
        newargv['mode'] = servcommand

        command = [sys.executable, '-m', 'tinyssg', '--config', f"{json.dumps(newargv)}", 'config']

        process = subprocess.Popen(
            command,
            stdout=None if not args['nolog'] else subprocess.PIPE,
            stderr=None if not args['nolog'] else subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        time.sleep(1)

        if process.poll() is None:
            return process
        else:
            TinySSGUtility.log_print('Server start failed.')
            TinySSGDebug.stop_server(process)
            return None

    @classmethod
    def open_browser(cls, args: dict) -> None:
        """
        Open the browser or Display Jupyter Iframe
        """
        url = f"http://localhost:{args['port']}/{args['output']}/"

        is_jupyter = False

        try:
            from IPython import get_ipython  # type: ignore
            env = get_ipython().__class__.__name__
            if env == 'ZMQInteractiveShell':
                is_jupyter = True
        except:  # noqa: E722
            pass

        if is_jupyter:
            from IPython import display
            display.display(display.IFrame(url, width=args['jwidth'], height=args['jheight']))
        else:
            webbrowser.open(url)

    @classmethod
    def launcher_start(cls, args: dict) -> None:
        """
        Launch the debug server and file change detection
        """
        if isinstance(args['curdir'], str) and len(args['curdir']) > 0:
            os.chdir(args['curdir'])

        cur_dir = os.getcwd()
        page_dir = os.path.join(cur_dir, args['page'])
        static_dir = os.path.join(cur_dir, args['static'])
        lib_dir = os.path.join(cur_dir, args['lib'])
        mod_time = 0.0
        should_reload = False

        if not os.path.isdir(page_dir):
            raise TinySSGException(f"The specified page directory does not exist. ({page_dir})")

        check_dirs = [page_dir]

        if os.path.isdir(static_dir):
            check_dirs.append(static_dir)

        if os.path.isdir(lib_dir):
            check_dirs.append(lib_dir)

        if not args['noreload']:
            _, mod_time = cls.check_for_changes(0.0, args, check_dirs)

        process = cls.launch_server(args, False)

        if process is None:
            return

        if not args['noopen']:
            cls.open_browser(args)

        while True:
            try:
                time.sleep(1)
                if process.poll() is not None:
                    TinySSGUtility.log_print('Server stopped.')
                    TinySSGDebug.server_stop_output(process)
                    break
                if not args['noreload']:
                    should_reload, mod_time = cls.check_for_changes(mod_time, args, check_dirs)
                if should_reload:
                    TinySSGUtility.log_print('File changed. Reloading...')
                    TinySSGDebug.stop_server(process)
                    time.sleep(1)
                    process = cls.launch_server(args, True)
            except KeyboardInterrupt:
                TinySSGDebug.stop_server(process)
                TinySSGUtility.error_print('Server stopped.')
                TinySSGDebug.server_stop_output(process)
                break


class TinySSG:
    """
    TinySSG Main Class
    """
    @classmethod
    def main(cls, args: dict) -> None:
        """
        Main function
        """
        exitcode = 0

        try:
            if args['mode'] == 'gen':
                if args['input'] == '':
                    TinySSGUtility.clear_start(args)
                TinySSGGenerator.generator_start(args)
                TinySSGUtility.log_print('HTML files generated.')
            elif args['mode'] == 'dev':
                TinySSGLauncher.launcher_start(args)
            elif args['mode'] == 'cls':
                TinySSGUtility.clear_start(args)
                TinySSGUtility.log_print('Output directory cleared.')
            elif args['mode'] == 'serv' or args['mode'] == 'servreload':
                TinySSGDebug.server_start(args)
            elif args['mode'] == 'config':
                config = json.loads(args['config'])
                default_args = cls.get_default_arg_dict()
                for key, value in default_args.items():
                    if key not in config:
                        config[key] = value
                cls.main(config)
            else:
                raise TinySSGException('Invalid mode.')
        except TinySSGException as e:
            TinySSGUtility.error_print(f"Error: {e}")
            exitcode = 1

        sys.exit(exitcode)

    @classmethod
    def get_arg_parser(cls) -> argparse.ArgumentParser:
        """
        Set the argument parser
        """
        parser = argparse.ArgumentParser(prog='python -m tinyssg', description='TinySSG Simple Static Site Generate Tool')
        parser.add_argument('mode', choices=['dev', 'gen', 'cls', 'serv', 'servreload', 'config'], help='Select the mode to run (gen = Generate HTML files, dev = Run the debug server)')
        parser.add_argument('--page', '-p', type=str, default='pages', help='Page file path')
        parser.add_argument('--static', '-s', type=str, default='static', help='Static file path')
        parser.add_argument('--lib', '-l', type=str, default='libs', help='Library file path')
        parser.add_argument('--output', '-o', type=str, default='dist', help='Output directory path')
        parser.add_argument('--input', '-i', type=str, default='', help='Input file name (Used to generate specific files only)')
        parser.add_argument('--curdir', '-C', type=str, default='', help='Current directory')
        parser.add_argument('--port', '-P', type=int, default=8000, help='Port number for the debug server')
        parser.add_argument('--wait', '-w', type=int, default=5, help='Wait time for file change detection')
        parser.add_argument('--nolog', '-n', action='store_true', help='Do not output debug server log')
        parser.add_argument('--noreload', '-r', action='store_true', help='Do not reload the server when the file changes')
        parser.add_argument('--noopen', '-N', action='store_true', help='Do not open the browser when starting the server')
        parser.add_argument('--config', '-c', type=str, default='', help='Configuration json string')
        parser.add_argument('--jwidth', '-jw', type=str, default='600', help='Jupyter iframe width')
        parser.add_argument('--jheight', '-jh', type=str, default='600', help='Jupyter iframe height')

        return parser

    @classmethod
    def get_default_arg_dict(cls):
        parser = cls.get_arg_parser()
        return vars(parser.parse_args(['dev']))

    @classmethod
    def cli_main(cls):
        """
        Command line interface
        """
        parser = cls.get_arg_parser()
        parse_args = parser.parse_args()
        args = vars(parse_args)
        cls.main(args)


if __name__ == '__main__':
    TinySSG.cli_main()
