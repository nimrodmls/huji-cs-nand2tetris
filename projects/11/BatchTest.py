import os
import subprocess

import JackCompiler

TARGET_DIR_PATH = r"C:\Projects\huji-cs-nand2tetris\projects\11"

def batch_test_directory(target_dir_path):
    JackCompiler.main(target_dir_path)

def main():
    subdirectories = list(os.walk(TARGET_DIR_PATH))[0][1]
    for subdirectory in subdirectories:
        directory = os.path.join(TARGET_DIR_PATH, subdirectory)
        batch_test_directory(directory)

if __name__ == "__main__":
    main()