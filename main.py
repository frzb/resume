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
        self.include_private_data = include_private_data
        self.json_path_private = os.path.abspath("input/private/private_resume.json")

        # Jinja template Environment
        self.env = Environment(
            loader=FileSystemLoader(os.path.dirname("input/templates/template.j2")),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=select_autoescape(["html", "xml"]),
        )
        # Render output on startup
        print("Render on startup")
        self.create_output()

    def create_output(self):
        for file in os.listdir("./input"):
            print(file)
            if file.endswith(".json"):
                name = f"_{os.path.splitext(os.path.basename(file))[0]}"
                data = self.load_data(f"./input/{file}", self.include_private_data)
                output_html_path = self.render_template(data, file)
                self.tailwindcss_build()
                HTML(output_html_path).write_pdf(f"./output/{name}.pdf")

    def on_closed(self, event):
        print(event)
        # if event.src_path in ["./input/resume.json", "./input/templates/template.j2"]:
        if event.src_path in ["./input"]:
            print(f"Detected relevant changes in {event.src_path}")
            self.create_output()

    def merge_dicts(self, dict1, dict2):
        for key, value in dict2.items():
            if (
                key in dict1
                and isinstance(dict1[key], dict)
                and isinstance(value, dict)
            ):
                dict1[key] = self.merge_dicts(dict1[key], value)
            else:
                dict1[key] = value
        return dict1

    def load_data(self, file, include_private_data=False):
        try:
            # Load the updated resume data from the JSON file
            print(file)
            with open(file) as json_file:
                resume_data = json.load(json_file)
            if include_private_data:
                print("Including private data")
                with open(self.json_path_private) as json_file:
                    self.resume_data_private = json.load(json_file)
                    merged = self.merge_dicts(file, self.resume_data_private)
                    resume_data = merged
            print("JSON resume data")
            print(resume_data)
            return resume_data
        except Exception as e:
            print(f"Error loading data from {file}: {e}")
            exit(1)

    def tailwindcss_build(self):
        # We needed to minify the Tailwiwind CSS file because
        # Weasyprint has issues with parsing nested CSS comments
        command = "poetry run tailwindcss --minify -i input/css/input.css -o static/css/tailwind.css"
        try:
            result = subprocess.run(
                command, check=True, capture_output=True, text=True, shell=True
            )
            print(result.stdout)
            print(result.stderr)
            print("Tailwind CSS compiled successfully:")
        except subprocess.CalledProcessError as e:
            print("Error occurred while running Tailwind CSS:")
            print(e.stderr)

    def render_template(self, data, file):
        try:
            # Load the template
            template_name = os.path.basename("templates/template.j2")
            template = self.env.get_template(template_name)

            if not "de" in file:
                output_html_path = os.path.abspath("./index.html")
                # Render the template with the resume data
                rendered_html = template.render(data)
                # Write the rendered HTML to the output file
                with open(output_html_path, "w") as output_file:
                    output_file.write(rendered_html)
            else:
                output_html_path = os.path.abspath("./index_de.html")
                # Render the template with the resume data
                rendered_html = template.render(data)
                # Write the rendered HTML to the output file
                with open(output_html_path, "w") as output_file:
                    output_file.write(rendered_html)

            print(f"Rendered HTML written to {output_html_path}")
            print(f"You can view your rendered resume at: file://{output_html_path}")
            webbrowser.open(output_html_path, new=2)
            return output_html_path
        except Exception as e:
            print(f"Error rendering template: {e}")
            exit(1)


class ResumeWatcher:
    def __init__(self, include_private_data):
        self.event_handler = ResumeHandler(include_private_data)
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
        include_private_data = ctx.obj.get("include_private_data", False)
        watcher = ResumeWatcher(include_private_data=include_private_data)
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
    # Create output directory
    try:
        os.makedirs("./output", exist_ok=True)
    except OSError as e:
        print(f"Error creating directory: {e}")

    build()
