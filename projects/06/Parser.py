"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
from typing import List, Tuple, TextIO
import SymbolTable

class Parser:
    """Encapsulates access to the input code. Reads an assembly program
    by reading each command line-by-line, parses the current command,
    and provides convenient access to the commands components (fields
    and symbols). In addition, removes all white space and comments.
    """
    COMMENT_NOTATION = "//"
    A_COMMAND_PREFIX = "@"
    WORD_LEN = 16

    COMP_COMMAND_PREFIX = "1"

    COMP_OPCODES = {"0": "110101010",
                    "1": "110111111",
                    "-1": "110111010",
                    "D": "110001100",
                    "A": "110110000",
                    "!D": "110001101",
                    "!A": "110110001",
                    "-D": "110001111",
                    "-A": "110110011",
                    "D+1": "110011111",
                    "A+1": "110110111",
                    "D-1": "110001110",
                    "A-1": "110110010",
                    "D+A": "110000010",
                    "D-A": "110010011",
                    "A-D": "110000111",
                    "D&A": "110000000",
                    "D|A": "110010101",
                    "M": "111110000",
                    "!M": "111110001",
                    "-M": "111110011",
                    "M+1": "111110111",
                    "M-1": "111110010",
                    "D+M": "111000010",
                    "D-M": "111010011",
                    "M-D": "111000111",
                    "D&M": "111000000",
                    "D|M": "111010101",
                    "A<<": "010100000",
                    "D<<": "010110000",
                    "M<<": "011100000",
                    "A>>": "010000000",
                    "D>>": "010010000",
                    "M>>": "011000000"}
    
    OPT_OPCODE  = "null" # Marking an optional opcode as part of the C command

    JMP_OPCODES = {OPT_OPCODE: "000",
                   "JGT": "001",
                   "JEQ": "010",
                   "JGE": "011",
                   "JLT": "100",
                   "JNE": "101",
                   "JLE": "110",
                   "JMP": "111"}
    
    DEST_OPCODES = {OPT_OPCODE: "000",
                    "M": "001",
                    "D": "010",
                    "MD": "011",
                    "A": "100",
                    "AM": "101",
                    "AD": "110",
                    "AMD": "111"}

    def __init__(self, input_file: TextIO) -> None:
        """Opens the input file and gets ready to parse it.

        Args:
            input_file (typing.TextIO): input file.
        """
        self._code, self._symbol_manager = \
            Parser._prepare_code(input_file.read().splitlines())
        self._current_line_index = 0
        self._next_available_address = 16

    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        return not (len(self._code) == self._current_line_index)

    def get_next_command(self) -> str:
        """
        This function has to be called only if has_more_commands is True,
        otherwise index error will be thrown.
        This function replaces the original 'advance', 'command_type', 'symbol', 
        'dest' & 'comp' functions. And is more "blackbox" for the user.
        """
        current_line = self._code[self._current_line_index]
        hack_command = ""
        # This is a A Command
        if current_line.startswith(Parser.A_COMMAND_PREFIX):
            hack_command = self._handle_A_command(current_line[1:])
        else: # This is a C Command
            hack_command = self._handle_C_command(current_line)

        # Incrementing the current line index
        self._current_line_index += 1

        return hack_command

    def _handle_A_command(self, command: str) -> str:
        """
        """
        address = 0
        if command.isdecimal():
            address = int(command)
        else:
            if self._symbol_manager.contains(command):
                address = self._symbol_manager.get_address(command)
            else:
                address = self._next_available_address
                self._symbol_manager.add_entry(command, address)
                # Incrementing the next available address, for when a new
                # symbol appears
                self._next_available_address += 1

        return Parser._pad_command(bin(address)[2:])

    def _handle_C_command(self, command: str) -> str:
        """
        KeyError may be raised if the current command had any invalid assembly
        procedures
        """
        command_dest = Parser.OPT_OPCODE
        command_jmp = Parser.OPT_OPCODE
        command_comp = ""

        command_part1 = command.split("=")
        command_part2 = []
        if 2 == len(command_part1):
            command_dest = command_part1[0]
            command_part2 = command_part1[1].split(";")
        else:
            command_part2 = command_part1[0].split(";")
            
        command_comp = command_part2[0]
        if 2 == len(command_part2):
            command_jmp = command_part2[1]

        # The C Command does not support both dest and jmp fields being null
        # (e.g. commands like 'D' or 'M' alone)
        if ((Parser.OPT_OPCODE == command_dest) and 
            (Parser.OPT_OPCODE == command_jmp)):
            raise Exception
        
        return Parser.COMP_COMMAND_PREFIX + \
               Parser.COMP_OPCODES[command_comp] + \
               Parser.DEST_OPCODES[command_dest] + \
               Parser.JMP_OPCODES[command_jmp]

    @staticmethod
    def _pad_command(command: str) -> str:
        """
        Pads the given command to the standard word length as defined in the
        specification of the Hack Computer
        """
        padded = command
        while Parser.WORD_LEN != len(padded):
            padded = "0" + padded

        return padded

    @staticmethod
    def _prepare_code(input_code: List[str]) -> Tuple[List[str], SymbolTable.SymbolTable]:
        """
        Removes comments, strips whitespaces & translates labels
        """
        symbol_manager = SymbolTable.SymbolTable()
        ready_code = []
        for current_line in input_code:
            # Removing whitespaces from everywhere
            current_line = current_line.replace("\t", "")
            current_line = current_line.replace(" ", "")

            # Checking if line is a comment
            comment_index = current_line.find(Parser.COMMENT_NOTATION)
            if -1 != comment_index:
                # Strip the line from everything past the comment
                current_line = current_line[:comment_index]

            # Checking if we landed on a label
            if current_line.startswith("("):
                # If the line doesn't end with an enclosing bracket, then
                # this is not a proper label command, we throw an error
                if not current_line.endswith(")"):
                    raise Exception
                
                symbol_manager.add_entry(current_line.strip("()"), len(ready_code))
            else:
                if 0 != len(current_line):
                    ready_code.append(current_line)

        return ready_code, symbol_manager

