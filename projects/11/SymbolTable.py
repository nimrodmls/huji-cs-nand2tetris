"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
from JackConstants import JackVariableTypes, JackKeywords

class VariableKinds:
    """
    A class to hold the different kinds of symbols in the Jack language.
    """
    STATIC = JackKeywords.STATIC
    FIELD = JackKeywords.FIELD
    ARG = "ARG"
    VAR = "VAR"
    
    SUBROUTINE_KINDS = [ARG, VAR]
    CLASS_KINDS = [STATIC, FIELD]
    ALL = [STATIC, FIELD, ARG, VAR]

class Symbol:
    """
    """

    def __init__(self, name: str, type: str, kind: str, index: int) -> None:
        """
        Args:
            name (str): the name of the new identifier.
            type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
            index (int): the index of the new identifier.
        """
        self.name = name
        self.type = type
        self.kind = kind
        self.index = index

    def __repr__(self) -> str:
        return f"Symbol({self.name}, {self.type}, {self.kind}, {self.index})"

class Subroutine:
    """
    """

    def __init__(self, name: str, return_type: str, kind: str) -> None:
        """
        Args:
            name (str): the name of the new subroutine.
            return_type (str): the return type of the new subroutine.
            kind (str): the kind of the new subroutine, can be:
            "CONSTRUCTOR", "FUNCTION", "METHOD".
        """
        self.name = name
        self.return_type = return_type
        self.kind = kind

    def __repr__(self) -> str:
        return f"Subroutine({self.name}, {self.return_type}, {self.kind})"

class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """

    def __init__(self) -> None:
        """Creates a new empty symbol table."""
        self._class_symbols = {}
        self._subroutine_symbols = {}
        self._var_count = {kind: 0 for kind in VariableKinds.ALL}

    def __enter__(self) -> "SymbolTable":
        """
        Opens a new subroutine scope (i.e. resets the subroutine's symbol table).
        """
        self._subroutine_symbols = {}
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Closes the current subroutine scope (erasing the subroutine's symbol table).
        """
        self._subroutine_symbols = {}

    def __getitem__(self, name: str) -> Symbol:
        """
        Retrieves a symbol from the symbol table by name.
        """
        return self.get_symbol(name)

    def __repr__(self) -> str:
        """
        Pretty prints the current symbol table.
        """
        out = 'Symbol Table:\n'
        out += '\tClass Symbols:\n'
        for name, symbol in self._class_symbols.items():
            out += f"\t\t{symbol}\n"
        out += '\tSubroutine Symbols:\n'
        for name, symbol in self._subroutine_symbols.items():
            out += f"\t\t{symbol}\n"
        return out
    
    def print_class_symbols(self) -> None:
        """
        Prints the class symbols.
        """
        print("Class Symbols:")
        for name, symbol in self._class_symbols.items():
            print(f"\t{symbol}")

    def print_subroutine_symbols(self) -> None:
        """
        Prints the subroutine symbols.
        """
        print("Subroutine Symbols:")
        for name, symbol in self._subroutine_symbols.items():
            print(f"\t{symbol}")

    def define(self, name: str, type: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns 
        it a running index. "STATIC" and "FIELD" identifiers have a class scope, 
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """
        symbol = Symbol(name, type, kind, self.var_count(kind))
        if kind in VariableKinds.CLASS_KINDS:
            self._class_symbols[name] = symbol
        elif kind in VariableKinds.SUBROUTINE_KINDS:
            self._subroutine_symbols[name] = symbol
        else:
            raise ValueError(f"SymbolTable: Encountered unknown kind - {kind}")
        self._var_count[kind] += 1
        
    def get_symbol(self, name: str) -> Symbol:
        """
        Returns the symbol associated with the given name.
        The symbol is searched for in the subroutine scope first, and then in
        the class scope.

        :param name: the name of the symbol to retrieve.
        """
        if name in self._subroutine_symbols:
            return self._subroutine_symbols[name]
        elif name in self._class_symbols:
            return self._class_symbols[name]
        else:
            raise ValueError(f"SymbolTable: Encountered unknown symbol - {name}")

    def var_count(self, kind: str) -> int:
        """
        Args:
            kind (str): can be "STATIC", "FIELD", "ARG", "VAR".

        Returns:
            int: the number of variables of the given kind already defined in 
            the current scope.
        """
        return self._var_count[kind]

    def kind_of(self, name: str) -> str:
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str: the kind of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """
        # Your code goes here!
        pass

    def type_of(self, name: str) -> str:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope.
        """
        # Your code goes here!
        pass

    def index_of(self, name: str) -> int:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            int: the index assigned to the named identifier.
        """
        # Your code goes here!
        pass

if __name__ == "__main__":
    # The following is a test for the SymbolTable class.
    symbol_table = SymbolTable()
    with symbol_table:
        symbol_table.define("x", JackVariableTypes.INT, VariableKinds.VAR)
        symbol_table.define("y", JackVariableTypes.BOOLEAN, VariableKinds.STATIC)
        symbol_table.define("z", JackVariableTypes.CHAR, VariableKinds.FIELD)
        print(symbol_table._class_symbols)
        print(symbol_table._subroutine_symbols)

    print("After")
    print(symbol_table._class_symbols)
    print(symbol_table._subroutine_symbols)