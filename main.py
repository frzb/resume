import json
import os
import time
import webbrowser
import subprocess
import click

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML


class ResumeHandler(FileSystemEventHandler):
    def __init__(self, include_private_data):
        self.json_path = os.path.abspath("input/resume.json")
        self.json_path_private = os.path.abspath("input/private/private_resume.json")
        # Jinja template Environment
        self.env = Environment(
            loader=FileSystemLoader(os.path.dirname("input/templates/template.html")),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Render output on startup
        print("Render on startup")
        self.load_data(include_private_data)
        self.render_template()
        self.tailwindcss_build()

    def on_closed(self, event):
        print(event)
        if event.src_path in ["./input/resume.json", "./input/templates/template.html"]:
            print(f"Detected relevant changes in {event.src_path}")
            self.load_data(include_private_data)
            self.render_template()
            self.tailwindcss_build()
            HTML("./output/output_resume.html").write_pdf("./output/resume.pdf")

    def merge_dicts(self, dict1, dict2):
        """
        Recursively merge two dictionaries. Values from dict2 overwrite those in dict1.
        """
        for key, value in dict2.items():
            if (
                key in dict1
                and isinstance(dict1[key], dict)
                and isinstance(value, dict)
            ):
                self.merge_dicts(dict1[key], value)
            else:
                dict1[key] = value
        return dict1

    def load_data(self, include_private_data=False):
        try:
            # Load the updated resume data from the JSON file
            with open(self.json_path) as json_file:
                self.resume_data = json.load(json_file)
            if include_private_data:
                print("Including private data")
                with open(self.json_path_private) as json_file:
                    self.resume_data_private = json.load(json_file)
                    self.merged = self.merge_dicts(
                        self.resume_data, self.resume_data_private
                    )
                    self.resume_data = self.merged
            print("JSON resume data")
            print(self.resume_data)
        except Exception as e:
            print(f"Error loading data from {self.json_path}: {e}")

    def tailwindcss_build(self):
        # We needed to minify the Tailwiwind CSS file because
        # Weasyprint has issues with parsing nested CSS comments
        command = "poetry run tailwindcss --minify -i input/css/input.css -o static/css/tailwind.css"
        try:
            result = subprocess.run(
                command, check=True, capture_output=True, text=True, shell=True
            )
            print("Tailwind CSS compiled successfully:")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print("Error occurred while running Tailwind CSS:")
            print(e.stderr)

    def render_template(self):
        try:
            # Load the template
            template_name = os.path.basename("templates/template.html")
            template = self.env.get_template(template_name)
            output_html_path = os.path.abspath("output/output_resume.html")

            # Render the template with the resume data
            rendered_html = template.render(self.resume_data)
            # Write the rendered HTML to the output file
            with open(output_html_path, "w") as output_file:
                output_file.write(rendered_html)

            print(f"Rendered HTML written to {output_html_path}")
            print(f"You can view your rendered resume at: file://{output_html_path}")
            webbrowser.open(output_html_path, new=2)
        except Exception as e:
            print(f"Error rendering template: {e}")
            exit(1)


class ResumeWatcher:
    def __init__(self, include_private_data):
        self.event_handler = ResumeHandler(self.include_private_data)
        self.observer = Observer()

    def start(self):
        self.observer.schedule(self.event_handler, path="./input", recursive=True)
        self.observer.start()
        print(f"Watching for changes in ...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

        self.observer.join()

    def stop(self):
        self.observer.stop()
        print("Stopped watching.")


@click.group(invoke_without_command=True)
@click.option("--include-private-data", is_flag=True, help="Include private data")
@click.pass_context
def build(ctx, include_private_data):
    """
    Watch for file changes, trigger automatic build
    """
    ctx.ensure_object(dict)
    ctx.obj["include_private_data"] = include_private_data
    if not ctx.invoked_subcommand:
        watcher = ResumeWatcher(include_private_data=ctx.obj["include_private_data"])
        watcher.start()


@build.command()
@click.pass_context
def one_shot(ctx):
    """
    Build CSS file and render Jinja template one time and exit
    """
    include_private_data = ctx.obj.get("include_private_data", False)
    ResumeHandler(include_private_data=include_private_data)


if __name__ == "__main__":
    build()
