import json
import os
import time
import webbrowser
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jinja2 import Environment, FileSystemLoader, select_autoescape


class ResumeHandler(FileSystemEventHandler):
    def __init__(self):
        self.json_path = os.path.abspath("input/resume.json")
        # Jinja template Environment
        self.env = Environment(
            loader=FileSystemLoader(os.path.dirname("input/templates/template.html")),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Render output on startup
        print("Render on startup")
        self.load_data()
        self.render_template()
        self.tailwindcss_build()

    def on_modified(self, event):
        print(event)
        if event.src_path in ['./input/resume.json', './input/templates/template.html']:
            print(f"Detected relevant changes in {event.src_path}")
            self.load_data()
            self.render_template()
            self.tailwindcss_build()

    def load_data(self):
        try:
            # Load the updated resume data from the JSON file
            with open(self.json_path) as json_file:
                self.resume_data = json.load(json_file)
            print("JSON resume data")
            print(self.resume_data)
        except Exception as e:
            print(f"Error loading data from {self.json_path}: {e}")

    def tailwindcss_build(self):
        command = "poetry run tailwindcss -o static/css/tailwind.css"
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
    def __init__(self):
        self.event_handler = ResumeHandler()
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


if __name__ == "__main__":
    watcher = ResumeWatcher()

    watcher.start()
