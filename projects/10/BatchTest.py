import os
import subprocess

import JackAnalyzer

TEXT_COMPARER_PATH = r"C:\projects\huji-cs-nand2tetris\tools\textcomparer.bat"
TARGET_DIR_PATH = r"C:\Users\nimro\Downloads\IfDo-20240307T093319Z-001"

def batch_test_directory(target_dir_path):
    # Generating XMLs
    JackAnalyzer.main(target_dir_path)

    # Now comparing the generated XMLs to the expected XMLs
    files_to_test = [
        os.path.join(target_dir_path, filename)
        for filename in os.listdir(target_dir_path)]
    
    for target_file in files_to_test:
        filename, extension = os.path.splitext(target_file)
        if extension.lower() != ".jack":
            continue
        target_cmp_file = os.path.join(target_dir_path, filename + ".xml")
        test_cmp_file = os.path.join(target_dir_path, filename + ".xml.cmp")
        res = subprocess.run(args=[TEXT_COMPARER_PATH, target_cmp_file, test_cmp_file], capture_output=True)
        if 'Comparison ended successfully' in str(res.stdout):
            print(f"\t>> Test {target_file} passed")
        else:
            print(f"\t>> Test {target_file} failed")

def main():
    subdirectories = list(os.walk(TARGET_DIR_PATH))[0][1]
    for subdirectory in subdirectories:
        directory = os.path.join(TARGET_DIR_PATH, subdirectory)
        #print(f"Testing directory {directory}")
        batch_test_directory(directory)

if __name__ == "__main__":
    main()