"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
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
    last until the line’s end.
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
        self._code = input_file.read().splitlines()
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
            # Stack-manipulating Commands
            "push": lambda segment, address: self._codewriter.vm_push(segment, int(address)),
            "pop": lambda segment, address: self._codewriter.vm_pop(segment, int(address)),
        }

    def get_next_command(self) -> Optional[str]:
        """
        Replaces has_more_commands() & advance() from the original template.
        """
        # Return None if we reached the end of the file
        if self._current_command_index >= len(self._code):
            return None
        
        # Iterating until we find a non-comment line
        ready_code = Parser._strip_comment(self._code[self._current_command_index])
        while 0 == len(ready_code):
            self._current_command_index += 1
            ready_code = Parser._strip_comment(self._code[self._current_command_index])
        ready_code = ready_code.split()

        # If we haven't found another line of code, after the comment, we will get
        # here and return None, means we got to the end of the file
        if 0 == len(ready_code):
            return None

        self._current_command_index += 1

        # The first element of ready_code is the VM command,
        # hence we get the proper handler for it, and call it
        return self._command_handlers[ready_code[0]](*ready_code[1:])

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

    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        # Your code goes here!
        pass

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current 
        command. Should be called only if has_more_commands() is true. Initially
        there is no current command.
        """
        # Your code goes here!
        pass

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current VM command.
            "C_ARITHMETIC" is returned for all arithmetic commands.
            For other commands, can return:
            "C_PUSH", "C_POP", "C_LABEL", "C_GOTO", "C_IF", "C_FUNCTION",
            "C_RETURN", "C_CALL".
        """
        # Your code goes here!
        pass

    def arg1(self) -> str:
        """
        Returns:
            str: the first argument of the current command. In case of 
            "C_ARITHMETIC", the command itself (add, sub, etc.) is returned. 
            Should not be called if the current command is "C_RETURN".
        """
        # Your code goes here!
        pass

    def arg2(self) -> int:
        """
        Returns:
            int: the second argument of the current command. Should be
            called only if the current command is "C_PUSH", "C_POP", 
            "C_FUNCTION" or "C_CALL".
        """
        # Your code goes here!
        pass
