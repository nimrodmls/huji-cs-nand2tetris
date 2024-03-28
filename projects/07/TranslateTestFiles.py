import os

import Main

def main():
    # base_path = "C:\\Projects\\huji-cs-nand2tetris\\Projects\\07"
    # files = ["MemoryAccess\\BasicTest\\BasicTest",
    #          "MemoryAccess\\PointerTest\\PointerTest",
    #          "MemoryAccess\\StaticTest\\StaticTest",
    #          "StackArithmetic\\SimpleAdd\\SimpleAdd",
    #          "StackArithmetic\\StackTest\\StackTest"]

    base_path = "C:\\Temp\\ex7_tests"
    files = [r"T3\T3",
             r"T2\T2",
             r"T1\T1",
             r"StackOverflowTest\StackTestOverflow",]
    for file in files:
        with open(os.path.join(base_path, file + ".vm"), "r") as vm_file, \
             open(os.path.join(base_path, file + ".asm"), "w") as out_file:
            Main.translate_file(vm_file, out_file)

if __name__ == "__main__":
    main()