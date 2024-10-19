import json
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jinja2 import Environment, FileSystemLoader, select_autoescape

class ResumeHandler(FileSystemEventHandler):
    def __init__(self, json_path, html_template_path, output_html_path):
        self.json_path = json_path
        self.html_template_path = html_template_path
        self.output_html_path = output_html_path
        self.env = Environment(loader=FileSystemLoader(os.path.dirname(html_template_path)),
                               autoescape=select_autoescape(['html', 'xml']))

        # Render output on startup
        print("Render on startup")
        self.load_data()
        self.render_template()

    def on_modified(self, event):
        if event.src_path == self.json_path:
            print(f"Detected changes in {self.json_path}, updating data...")
            self.load_data()
            self.render_template()
        elif event.src_path == self.html_template_path:
            print(f"Detected changes in {self.html_template_path}, reloading template...")


    def load_data(self):
        try:
            # Load the updated resume data from the JSON file
            with open(self.json_path) as f:
                self.resume_data = json.load(f)
            print("JSON resume data")
        except Exception as e:
            print(f"Error loading data from {self.json_path}: {e}")


    def update_data(self):
        try:
            # Load the updated resume data from the JSON file
            resume_data = self.resume_data
            print(resume_data)

            # Render the HTML template with the resume data
            self.render_template()
        except Exception as e:
            print(f"Error loading data from {self.json_path}: {e}")

    def render_template(self):
        try:
            # Load the template
            template_name = os.path.basename(self.html_template_path)
            template = self.env.get_template(template_name)

            # Render the template with the resume data
            rendered_html = template.render(self.resume_data)
            # Write the rendered HTML to the output file
            with open(self.output_html_path, 'w') as output_file:
                output_file.write(rendered_html)

            print(f"Rendered HTML written to {self.output_html_path}")
            print(f"You can view your rendered resume at:  file://{self.output_html_path}")
        except Exception as e:
            print(f"Error rendering template: {e}")
            exit(1)

class ResumeWatcher:
    def __init__(self, json_path, html_template_path, output_html_path):
        self.json_path = json_path
        self.html_template_path = html_template_path
        self.output_html_path = output_html_path
        self.event_handler = ResumeHandler(json_path, html_template_path, output_html_path)
        self.observer = Observer()

    def start(self):
        self.observer.schedule(self.event_handler, path=os.path.dirname(self.json_path), recursive=False)
        self.observer.schedule(self.event_handler, path=os.path.dirname(self.html_template_path), recursive=False)
        self.observer.start()
        print(f"Watching for changes in {self.json_path} and {self.html_template_path}...")
        try:
            while True:
                time.sleep(1)  # Keep the script running
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.observer.stop()
        self.observer.join()
        print("Stopped watching.")

if __name__ == "__main__":
    json_path = os.path.abspath('resume.json')  # Path to your JSON file
    html_template_path = os.path.abspath('templates/template.html')  # Path to your HTML template
    output_html_path = os.path.abspath('output_resume.html')  # Output HTML file path

    watcher = ResumeWatcher(json_path, html_template_path, output_html_path)
    watcher.start()

