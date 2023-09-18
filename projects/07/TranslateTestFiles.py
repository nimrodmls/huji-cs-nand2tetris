import os

import Main

def main():
    base_path = "C:\\Projects\\huji-cs-nand2tetris\\Projects\\07"
    files = ["MemoryAccess\\BasicTest\\BasicTest",
             "MemoryAccess\\PointerTest\\PointerTest",
             "MemoryAccess\\StaticTest\\StaticTest",
             "StackArithmetic\\SimpleAdd\\SimpleAdd",
             "StackArithmetic\\StackTest\\StackTest"]
    for file in files:
        with open(os.path.join(base_path, file + ".vm"), "r") as vm_file, \
             open(os.path.join(base_path, file + ".asm"), "w") as out_file:
            Main.translate_file(vm_file, out_file)

if __name__ == "__main__":
    main()