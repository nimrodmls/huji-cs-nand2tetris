"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
import SymbolTable

class Parser:
    """Encapsulates access to the input code. Reads an assembly program
    by reading each command line-by-line, parses the current command,
    and provides convenient access to the commands components (fields
    and symbols). In addition, removes all white space and comments.
    """
    COMMENT_NOTATION = "//"

    def __init__(self, input_file: typing.TextIO) -> None:
        """Opens the input file and gets ready to parse it.

        Args:
            input_file (typing.TextIO): input file.
        """
        self._code, self._symbol_manager = \
            Parser._prepare_code(input_file.read().splitlines())
        self._current_line_index = 0

    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        return len(self._code) == self._current_line_index

    def get_next_command(self) -> str:
        """
        This function has to be called only if has_more_commands is True,
        otherwise index error will be thrown.
        This function replaces the original 'advance', 'command_type', 'symbol', 
        'dest' & 'comp' functions. And is more "blackbox" for the user.
        """

        # Incrementing the current line index
        self._current_line_index += 1

    @staticmethod
    def _prepare_code(input_code: typing.List[str]) -> typing.List[str]:
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
                
                symbol_manager.add_entry(current_line.strip("()"), len(ready_code) + 1)
            else:
                if 0 != len(current_line):
                    ready_code.append(current_line)

        return ready_code, symbol_manager

    #############################################
    # CODE FROM THE ORIGINAL TEMPLATE - UNUSED! #
    #############################################

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current command.
        Should be called only if has_more_commands() is true.
        """
        # Your code goes here!
        pass

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current command:
            "A_COMMAND" for @Xxx where Xxx is either a symbol or a decimal number
            "C_COMMAND" for dest=comp;jump
            "L_COMMAND" (actually, pseudo-command) for (Xxx) where Xxx is a symbol
        """
        # Your code goes here!
        pass

    def symbol(self) -> str:
        """
        Returns:
            str: the symbol or decimal Xxx of the current command @Xxx or
            (Xxx). Should be called only when command_type() is "A_COMMAND" or 
            "L_COMMAND".
        """
        # Your code goes here!
        pass

    def dest(self) -> str:
        """
        Returns:
            str: the dest mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        # Your code goes here!
        pass

    def comp(self) -> str:
        """
        Returns:
            str: the comp mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        # Your code goes here!
        pass

    def jump(self) -> str:
        """
        Returns:
            str: the jump mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        # Your code goes here!
        pass
