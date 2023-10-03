import os

import Main

def main():
    base_path = "C:\\Projects\\huji-cs-nand2tetris\\Projects\\08"
    directories = ["FunctionCalls\\FibonacciElement",
                   "FunctionCalls\\NestedCall",
                   "FunctionCalls\\SimpleFunction",
                   "FunctionCalls\\StaticsTest",
                   "ProgramFlow\\FibonacciSeries",
                   "ProgramFlow\\BasicLoop"]
    for directory in directories:
        Main.main(os.path.join(base_path, directory))

if __name__ == "__main__":
    main()