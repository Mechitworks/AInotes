import os
import requests
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
path = Path(__file__).parent.absolute()
print(path)
# Load instruction set
with open("instruction_set.txt", "r") as file:
    instruction_set = file.read()


# Function to get the folder structure
def get_folder_structure(root_dir):
    folder_structure = {}
    for root, dirs, files in os.walk(root_dir):
        # Use relative paths instead of absolute paths
        rel_root = os.path.relpath(root, root_dir)
        if rel_root == ".":
            rel_root = ""
        folder_structure[rel_root] = {"dirs": dirs, "files": files}
    return folder_structure


# Function to connect to LLaMA 7B API
def get_ai_response(note_content, instruction_set, folder_structure, filename):
    api_url = "http://localhost:11434/api/generate"  # Replace with your actual API URL
    prompt = f"Instruction: {instruction_set}\nFilename: {filename}\nNote: {note_content}\nFolder Structure: {folder_structure}"
    payload = {
        "model": "llama3.1",
        "stream": False,
        "prompt": prompt,
    }
    logging.debug(f"Payload sent to AI: {payload}")
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        responsetext = response.json().get("response", {})
        logging.debug(f"Response received from AI: {responsetext}")
        return response.json().get("response", {})
    except requests.RequestException as e:
        logging.error(f"Error communicating with AI API: {e}")
        return {}


# Function to process AI commands
def process_commands(commands, note_file, note_content, path):
    comments = []
    file_placed = False
    for command in commands.split("\n"):
        parts = command.strip().split()
        if not parts:
            continue
        if parts[0] == "%%mkdir":
            newdir = "organized_notes/" + parts[1]
            try:
                os.makedirs(newdir, exist_ok=True)
            except OSError as e:
                logging.error(f"Error creating directory {parts[1]}: {e}")
        elif parts[0] == "%%placefile":
            logging.error(f"Placing file {parts[1]}")
            new_path = "organized_notes/" + parts[1]
            try:
                with open(new_path, "w") as file:
                    file.write(note_content)
                # os.remove(note_file)
                file_placed = True
            except OSError as e:
                logging.error(f"Error placing file {new_path}: {e}")
        elif parts[0] == "%%addtags":
            tags = parts[1].strip("()").split(",")
            tags_md = "\n".join([f"# {tag.strip()}" for tag in tags])
            note_content = f"{tags_md}\n\n{note_content}"
        elif parts[0] == "%%comment":
            comment = " ".join(parts[1:])
            comments.append(comment)

    # Add comments to the top of the note content
    if comments:
        comments_md = "\n".join([f"> {comment}" for comment in comments])
        note_content = f"{comments_md}\n\n{note_content}"

    # Check if note is saved
    if not file_placed:
        logging.error(f"Error saving note file {note_file} ")


# Process notes
notes_queue = "notes_queue/"
organized_notes = "organized_notes/"

# Get the current folder structure in organized_notes
folder_structure = get_folder_structure(organized_notes)

for note_file in os.listdir(notes_queue):
    if note_file.endswith(".md"):
        note_path = os.path.join(notes_queue, note_file)
        try:
            with open(note_path, "r") as file:
                note_content = file.read()
        except OSError as e:
            logging.error(f"Error reading note file {note_path}: {e}")
            continue

        ai_response = get_ai_response(note_content, instruction_set, folder_structure, note_file)
        # tags = ai_response.get("tags", [])
        commands = ai_response

        # Add tags to the start of the document in markdown format
        # tags_md = "\n".join([f"# {tag}" for tag in tags])
        # note_content = f"{tags_md}\n\n{note_content}"

        # Process AI commands
        process_commands(commands, note_path, note_content, path)

        # prompt user to press enter to continue
        # input("Press Enter to continue...")
