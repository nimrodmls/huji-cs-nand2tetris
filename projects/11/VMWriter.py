"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
from JackConstants import HACK_MAX_INT, HACK_MIN_INT, MIN_TEMP_SEGMENT, MAX_TEMP_SEGMENT

class VMMemorySegments:
    """
    A class to hold the different memory segments in the VM language.
    """
    CONST = "constant"
    ARG = "argument"
    LOCAL = "local"
    STATIC = "static"
    THIS = "this"
    THAT = "that"
    POINTER = "pointer"
    TEMP = "temp"
    ALL = [CONST, ARG, LOCAL, STATIC, THIS, THAT, POINTER, TEMP]

class VMArithmeticCommands:
    """
    A class to hold the different arithmetic commands in the VM language.
    """
    ADD = "add"
    SUB = "sub"
    NEG = "neg"
    EQ = "eq"
    GT = "gt"
    LT = "lt"
    AND = "and"
    OR = "or"
    NOT = "not"
    SHIFTLEFT = "shiftleft"
    SHIFTRIGHT = "shiftright"
    ALL = [ADD, SUB, NEG, EQ, GT, LT, AND, OR, NOT, SHIFTLEFT, SHIFTRIGHT]

class VMWriter:
    """
    Writes VM commands into a file. Encapsulates the VM command syntax.
    """

    def __init__(self, output_stream: typing.TextIO) -> None:
        """Creates a new file and prepares it for writing VM commands."""
        self._output_stream = output_stream

    def write_documentation(self, documentation: str) -> None:
        """Writes documentation to the output stream.

        :param documentation: the documentation to write.
        """
        self._write_line(f"// {documentation}")

    def write_push(self, segment: str, index: int) -> None:
        """Writes a VM push command.

        :param segment: the segment to push to, as defined in VMMemorySegments.
        :param index: the index to push to.
        """
        VMWriter._validate_memory_access(segment, index)
        self._write_line(f"push {segment} {index}")

    def write_pop(self, segment: str, index: int) -> None:
        """Writes a VM pop command.

        :param segment: the segment to pop from, as defined in VMMemorySegments.
        :param index: the index to pop from.
        """
        VMWriter._validate_memory_access(segment, index)
        self._write_line(f"pop {segment} {index}")

    def write_arithmetic(self, command: str) -> None:
        """Writes a VM arithmetic command.

        :param command: the command to write, as defined in VMArithmeticCommands.
        """
        if command not in VMArithmeticCommands.ALL:
            raise ValueError(f"VMWriter: Invalid arithmetic command {command}")
        
        self._write_line(command)

    def write_label(self, label: str) -> None:
        """Writes a VM label command.

        :param label: the name of the label to write.
        """
        self._write_line(f"label {label}")

    def write_goto(self, label: str) -> None:
        """Writes a VM goto command.

        :param label: the name of the label to go to.
        """
        self._write_line(f"goto {label}")

    def write_if_goto(self, label: str) -> None:
        """Writes a VM if-goto command.

        :parma label: the name of the label to go to if the condition is met.
        """
        self._write_line(f"if-goto {label}")

    def write_call(self, name: str, n_args: int) -> None:
        """Writes a VM call command.

        :param name: the name of the function to call.
        :param n_args: the number of arguments received by the function.
        """
        self._write_line(f"call {name} {n_args}")

    def write_function(self, name: str, n_locals: int) -> None:
        """Writes a VM function command.

        :param name: the name of the function.
        :param n_locals: the number of local variables the function uses.
        """
        self._write_line(f"function {name} {n_locals}")

    def write_return(self) -> None:
        """
        Writes a VM return command.
        """
        self._write_line("return")

    def _write_line(self, line: str) -> None:
        """
        Writes a line to the output stream.
        """
        self._output_stream.write(line + "\n")

    @staticmethod
    def _validate_memory_access(segment: str, index: int) -> None:
        """
        Validates the access to memory segments via Pop/Push commands.

        :param segment: the segment to access.
        :param index: the index to access.
        :raises ValueError: if the segment/index combination is invalid.
        """
        if segment not in VMMemorySegments.ALL:
            raise ValueError(f"VMWriter: Invalid segment {segment}")
        
        if segment == VMMemorySegments.CONST and (HACK_MIN_INT > index or index > HACK_MAX_INT):
            raise ValueError(f"VMWriter: Invalid constant {index}")
        
        if segment == VMMemorySegments.POINTER and index not in [0, 1]:
            raise ValueError(f"VMWriter: Invalid pointer {index}")
        
        if segment == VMMemorySegments.TEMP and (0 > index or (index > HACK_MAX_INT - MIN_TEMP_SEGMENT + 1)):
            raise ValueError(f"VMWriter: Invalid temp {index}")
