from os import listdir, path, makedirs, rmdir, remove
from collections import defaultdict
from subprocess import run, CalledProcessError
from send2trash import send2trash
from shutil import move
from random import choice
from string import ascii_lowercase


FILES_DIRECTORY = str(input("Enter the directory with your Live Photos: ")).strip(" '\"")
OUTPUT_DIRECTORY = str(input("Enter the output directory, or leave it blank to overwrite: ")).strip(" '\"")
SCRIPT_DIRECTORY = str(input("Enter the MotionPhoto2 directory: ")).strip(" '\"")
PHOTO_EXTS = {"heic", "jpg", "jpeg"}
VIDEO_EXTS = {"mov", "mp4"}
DRY_RUN = False
DELETE_ORIGINAL = False

if not path.exists(path.join(SCRIPT_DIRECTORY, "motionphoto2.py")):
    print("Error: motionphoto2.py not found in the specified script directory.")
    exit(1)

if not path.exists(FILES_DIRECTORY):
    print("Error, invalid files directory")
    exit(1)
    
if OUTPUT_DIRECTORY != "" and not path.exists(OUTPUT_DIRECTORY) and OUTPUT_DIRECTORY != FILES_DIRECTORY:
    print("Error, invalid output directory")
    exit(1)

if OUTPUT_DIRECTORY == "":
    while True:
        random_string = ''.join(choice(ascii_lowercase) for i in range(12))
        OUTPUT_DIRECTORY = path.join(FILES_DIRECTORY, random_string)
        if not path.exists(OUTPUT_DIRECTORY):
            makedirs(OUTPUT_DIRECTORY)
            break
        
    DELETE_ORIGINAL = True

quit = False

print(f"The script will look for {PHOTO_EXTS} to detect photos")
print("Would you like to check for more?")
user_choice = str(input("y(es)/n(o): "))
if "y" in user_choice:
    while not quit:
        ext = str(input("Enter the extension (example: jpg) here, or q(uit): "))
        ext = ext.lower()
        if ext in {"q", "quit", "", "stop"}:
            quit = True
        else:
            PHOTO_EXTS.add(ext)
            
quit = False
print(f"The script will look for {VIDEO_EXTS} to detect videos")
print("Would you like to check for more?")
user_choice = str(input("y(es)/n(o): "))
if "y" in user_choice:
    while not quit:
        ext = str(input("Enter the extension (example: mp4) here, or q(uit): "))
        ext = ext.lower()
        if ext in {"q", "quit", "", "stop"}:
            quit = True
        else:
            VIDEO_EXTS.add(ext)
            

dry_prompt = str(input("Run in dry-run mode? (y/n): ")).strip().lower()
if dry_prompt in {"y", "yes"}:
    DRY_RUN = True

files = listdir(FILES_DIRECTORY)
files.sort()
file_dict = defaultdict(list)

for file in files:
    filename = ".".join(file.split(".")[:-1])
    file_dict[filename].append(file)    

duplicates = {}

for base, names in file_dict.items():
    if len(names) > 1:
        duplicates[base] = names

for base, names in duplicates.items():
    image_file = video_file = None

    for name in names:
        ext = name.split(".")[-1].lower()
        if ext in PHOTO_EXTS:
            image_file = name
        elif ext in VIDEO_EXTS:
            video_file = name

    if image_file and video_file:
        image_path = path.join(FILES_DIRECTORY, image_file)
        video_path = path.join(FILES_DIRECTORY, video_file)
        
        if OUTPUT_DIRECTORY != "":
            output_file = path.join(OUTPUT_DIRECTORY, base)

        command = [
            "python3", path.join(SCRIPT_DIRECTORY, "motionphoto2.py"),
            "--input-image", image_path,
            "--input-video", video_path,
            "--output-file", output_file,
        ]
        
        if DRY_RUN:
            print(f"Would merge {base}")
            print(" ".join(command))
            continue

        
        try:
            print(f"Merging {base}")
            run(command, check=True)
            
        except CalledProcessError as e:
            print(f"Error processing {base}: {e}")
            
        if DELETE_ORIGINAL:
            send2trash(image_path)
            send2trash(video_path)
            output_files = listdir(FILES_DIRECTORY)
            output_file_index = -1
            for i in range(len(output_files)):
                if output_file in output_files[i]:
                    output_file_index = i
                    break
            if output_file_index != -1:
                full_output = output_files[output_file_index]
                move(full_output, path.join(FILES_DIRECTORY, base))
                if path.exists(full_output):
                    remove(full_output)
    else:
        print(f"Skipping {base}: Missing image or video file.")
        
if DELETE_ORIGINAL:
    try:
        rmdir(OUTPUT_DIRECTORY)
        print(f"Directory '{OUTPUT_DIRECTORY}' has been removed successfully")
    except OSError as e:
        print(f"Error: {OUTPUT_DIRECTORY} : {e.strerror}")