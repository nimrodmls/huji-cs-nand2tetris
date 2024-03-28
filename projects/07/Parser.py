"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import re

from CodeWriter import CodeWriter
from typing import Optional, TextIO

class Parser:
    """
    # Parser
    
    Handles the parsing of a single .vm file, and encapsulates access to the
    input code. It reads VM commands, parses them, and provides convenient 
    access to their components. 
    In addition, it removes all white space and comments.

    ## VM Language Specification

    A .vm file is a stream of characters. If the file represents a
    valid program, it can be translated into a stream of valid assembly 
    commands. VM commands may be separated by an arbitrary number of whitespace
    characters and comments, which are ignored. Comments begin with "//" and
    last until the line's end.
    The different parts of each VM command may also be separated by an arbitrary
    number of non-newline whitespace characters.

    - Arithmetic commands:
      - add, sub, and, or, eq, gt, lt
      - neg, not, shiftleft, shiftright
    - Memory segment manipulation:
      - push <segment> <number>
      - pop <segment that is not constant> <number>
      - <segment> can be any of: argument, local, static, constant, this, that, 
                                 pointer, temp
    - Branching (only relevant for project 8):
      - label <label-name>
      - if-goto <label-name>
      - goto <label-name>
      - <label-name> can be any combination of non-whitespace characters.
    - Functions (only relevant for project 8):
      - call <function-name> <n-args>
      - function <function-name> <n-vars>
      - return
    """

    COMMENT_NOTATION = "//"

    def __init__(self, input_file: TextIO) -> None:
        """Gets ready to parse the input file.

        Args:
            input_file (typing.TextIO): input file.
        """
        self._code = Parser._strip_all_comments(input_file.read()).splitlines()
        self._current_command_index = 0
        self._codewriter = CodeWriter()
        self._command_handlers = {
            # Arithmetic Commands
            "add": self._codewriter.vm_add,
            "sub": self._codewriter.vm_sub,
            "neg": self._codewriter.vm_neg,
            "eq": self._codewriter.vm_eq,
            "gt": self._codewriter.vm_gt,
            "lt": self._codewriter.vm_lt,
            "and": self._codewriter.vm_and,
            "or": self._codewriter.vm_or,
            "not": self._codewriter.vm_not,
            "shiftleft": self._codewriter.vm_shiftleft,
            "shiftright": self._codewriter.vm_shiftright,
            # Stack-manipulating Commands
            "push": lambda segment, address: self._codewriter.vm_push(segment, int(address)),
            "pop": lambda segment, address: self._codewriter.vm_pop(segment, int(address)),
        }

    def parse_translate(self):
        """
        """
        asm = []
        for command in self._code:
            command_tokens = command.split()

            # This command is empty, so we skip it
            if 0 == len(command_tokens):
                continue

            # The first element of the command tokens is the VM command,
            # hence we get the proper handler for it, and call it, with the
            # rest of the command tokens, if available
            asm += self._command_handlers[command_tokens[0]](*command_tokens[1:])
        
        return "\n".join(asm)

    @staticmethod
    def _strip_all_comments(code):
        """
        """
        return re.sub(r"//.*?$", " ", code, flags=re.MULTILINE)

    @staticmethod
    def _strip_comment(code_line: str) -> str:
        """
        """
        current_line = code_line
        comment_index = current_line.find(Parser.COMMENT_NOTATION)
        if -1 != comment_index:
            # Strip the line from everything past the comment
            current_line = current_line[:comment_index]
        return current_line
