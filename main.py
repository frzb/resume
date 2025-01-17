import json
import os
import time
import webbrowser
import subprocess
import click
from git import Repo
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright


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
        repo = Repo(search_parent_directories=True)
        self.env.globals.update({
            'short_git_sha': repo.head.object.hexsha[:7]
            })
        # Render output on startup
        print("Render on startup")
        self.create_output()

    def create_output(self):
        for file in os.listdir("./input"):
            if file.endswith(".json"):
                name = f"_{os.path.splitext(os.path.basename(file))[0]}"
                data = self.load_data(f"./input/{file}", self.include_private_data)
                output_html_path = self.render_template(data, file)
                self.tailwindcss_build()
                self.create_pdf(output_html_path, name)


    def on_closed(self, event):
        print(event)
        print(event.src_path)
        # VIM is writing a test file called 4913, so we need exclude this to trigger a build
        # https://github.com/vim/vim/blob/30377e0fe084496911e108cbb33c84cf075e6e33/src/bufwrite.c#L1210
        if "4913" not in event.src_path:
            print(f"Detected relevant changes in {event.src_path}")
            self.create_output()

    def create_pdf(self, url, file_name):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file:///{url}")
            page.emulate_media(media="print")
            # Waiting for the side to loaded matters, else the fallback font is applied
            page.wait_for_function("document.fonts.status === 'loaded'")
            page.pdf(path=f"./output/{file_name}.pdf", format="A4",landscape=False, margin={"top": "2cm"})
            browser.close()

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
            with open(file) as json_file:
                resume_data = json.load(json_file)
            if include_private_data:
                print("Including private data")
                with open(self.json_path_private) as json_file:
                    self.resume_data_private = json.load(json_file)
                    merged = self.merge_dicts(resume_data, self.resume_data_private)
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
                # JSON Resume has no proper I18N support
                # We do dirty search-and-replace for the headlines translation
                translations = [
                    ("Germany", "Deutschland"),
                    ("Work Experience", "Berufserfahrung"),
                    ("Education", "Ausbildung"),
                    ("Skills and Experience", "Kompetenzen und Erfahrung"),
                    ("Languages", "Sprachen"),
                ]
                for search_phrase, replacement in translations:
                    rendered_html = rendered_html.replace(search_phrase, replacement)

                # Write the rendered HTML to the output file
                with open(output_html_path, "w") as output_file:
                    output_file.write(rendered_html)

            print(f"Rendered HTML written to {output_html_path}")
            print(f"You can view your rendered resume at: file://{output_html_path}")
            webbrowser.open(output_html_path, new=0)
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
