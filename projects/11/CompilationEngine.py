"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
import JackTokenizer

from JackConstants import JackKeywords, JackSymbols, JackVariableTypes, HACK_MIN_INT, HACK_MAX_INT
from SymbolTable import Symbol, SymbolTable, VariableKinds
from VMWriter import VMMemorySegments, VMArithmeticCommands, VMWriter

class OS_API:
    """
    Handles the OS API calls for the Jack language.
    """
    
    def __init__(self, vm_writer: VMWriter) -> None:
        self._vm_writer = vm_writer

    def new_string(self, string_val: str) -> None:
        """
        Creates a new string object from the given string value.
        """
        self._vm_writer.write_push(VMMemorySegments.CONST, len(string_val))
        self._vm_writer.write_call('String.new', 1)
        for char in string_val:
            self._vm_writer.write_push(VMMemorySegments.CONST, ord(char))
            self._vm_writer.write_call('String.appendChar', 1)

class CompilationEngine:
    """
    Gets input from a JackTokenizer and emits its parsed structure into an output stream.
    All functions with vm prefix are used to write VM commands to the output stream.
    """

    # All the statements in the Jack language
    JACK_STATEMENTS = [JackKeywords.DO, JackKeywords.LET, JackKeywords.WHILE, 
                       JackKeywords.RETURN, JackKeywords.IF]
    
    # All the operators in the Jack language
    JACK_EXPRESSION_OPS = [JackSymbols.PLUS, JackSymbols.MINUS, JackSymbols.ASTERISK,
                            JackSymbols.SLASH, JackSymbols.AMPERSAND, JackSymbols.PIPE,
                            JackSymbols.LESS_THAN, JackSymbols.GREATER_THAN, JackSymbols.EQUALS]
    
    # All the unary operators in the Jack language
    JACK_UNARY_EXPRESSION_OPS = [JackSymbols.MINUS, JackSymbols.TILDE, 
                                 JackSymbols.SHIFT_LEFT, JackSymbols.SHIFT_RIGHT]
    
    # Mapping between the Jack variable types and the VM host memory segments
    SEGMENT_MAP = {
        JackKeywords.FIELD: VMMemorySegments.THIS,
        JackKeywords.STATIC: VMMemorySegments.STATIC,
        VariableKinds.ARG: VMMemorySegments.ARG,
        VariableKinds.VAR: VMMemorySegments.LOCAL
    }
    
    def __init__(self, input_stream: JackTokenizer.JackTokenizer, output_stream) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self._tokenizer = input_stream
        self._symbol_table: SymbolTable = SymbolTable()
        self._vm_writer = VMWriter(output_stream)
        self._os_api = OS_API(self._vm_writer)
        
    def finalize(self):
        self._symbol_table.print_class_symbols()

    def compile_class(self) -> None:
        """
        Compiles a complete class
        """
        if ('KEYWORD' != self._tokenizer.token_type()) or (JackKeywords.CLASS != self._tokenizer.keyword()):
            raise ValueError("CompilationEngine: Expected 'class' keyword")
        
        self._insert_keyword(JackKeywords.CLASS)
        self._tokenizer.advance()

        # Add the class name
        self._insert_identifier(self._tokenizer.identifier())
        self._tokenizer.advance()

        # Add the opening curly brace
        open_curly = self._tokenizer.symbol()
        if JackSymbols.OPENING_CURLY_BRACKET != open_curly:
            raise ValueError("CompilationEngine: Expected '{' symbol after class ID")
        self._insert_symbol(JackSymbols.OPENING_CURLY_BRACKET)
        self._tokenizer.advance()

        # Compile the class variables
        while ('KEYWORD' == self._tokenizer.token_type()) and \
              (self._tokenizer.keyword() in [JackKeywords.STATIC, JackKeywords.FIELD]):
            self.compile_class_var_dec()

        # Compile the subroutines
        while ('KEYWORD' == self._tokenizer.token_type()) and \
              (self._tokenizer.keyword() in [JackKeywords.CONSTRUCTOR, JackKeywords.FUNCTION, JackKeywords.METHOD]):
            self.compile_subroutine()

        # Add the closing curly brace
        close_curly = self._tokenizer.symbol()
        if JackSymbols.CLOSING_CURLY_BRACKET != close_curly:
            raise ValueError("CompilationEngine: Expected '}' symbol after class body")
        self._insert_symbol(JackSymbols.CLOSING_CURLY_BRACKET)
        self._tokenizer.advance()

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        # Expecting the static or field keyword
        if ('KEYWORD' != self._tokenizer.token_type()) or \
           (self._tokenizer.keyword() not in [VariableKinds.STATIC, VariableKinds.FIELD]):
            raise ValueError("CompilationEngine: Expected 'static' or 'field' keyword for class variables")
        
        var_kind = self._tokenizer.keyword()
        self._insert_keyword(self._tokenizer.keyword())
        self._tokenizer.advance()

        # Get the type
        var_type = self._handle_var_type()
        self._tokenizer.advance()

        # Add the variables to the Symbol Table
        self._add_variable_list(var_kind, var_type)

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        # Expecting the constructor, function, or method keyword
        func_type = self._tokenizer.keyword()
        self._tokenizer.advance()

        # Get the return type
        ret_type = self._handle_var_type(with_void=True)
        self._tokenizer.advance()

        # Get the subroutine name - we're not doing anything with it, 
        # it should be in some sort of a linker
        func_name = self._tokenizer.identifier()
        self._tokenizer.advance()

        # Starting the subroutine scope for the symbol table
        with self._symbol_table:

            # Validate the opening round bracket
            self._validate_symbol(self._tokenizer.symbol(), 
                                "CompilationEngine: Expected '(' symbol after subroutine name")
            self._tokenizer.advance()

            # Compile the parameter list - adding the parameters to the symbol table
            self.compile_parameter_list()

            # Validate the closing round bracket
            self._validate_symbol(self._tokenizer.symbol(), 
                                "CompilationEngine: Expected ')' symbol after subroutine parameter list")
            self._tokenizer.advance()

            self.compile_subroutine_body()

            # TODO: Remove
            self._symbol_table.print_subroutine_symbols()
        
    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        # We expect a closing parenthesis, thus ending the parameter list
        while ('SYMBOL' != self._tokenizer.token_type()) or \
              (JackSymbols.CLOSING_PARENTHESIS != self._tokenizer.symbol()):
            # Handling the parameter type
            param_type = self._handle_var_type()
            self._tokenizer.advance()

            # Handling the parameter name
            param_name = self._tokenizer.identifier()
            self._tokenizer.advance()

            # Adding the parameter to the symbol table
            self._symbol_table.define(param_name, param_type, VariableKinds.ARG)

            # Handling the separating comma, if it exists
            if JackSymbols.COMMA == self._tokenizer.symbol():
                self._insert_symbol(JackSymbols.COMMA)
                self._tokenizer.advance()

    def compile_subroutine_body(self) -> None:
        """
        Compiles the body of a subroutine (variable declarations, and then statements)
        """
        # Add the opening curly brace
        self._validate_symbol(JackSymbols.OPENING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '{' symbol after subroutine declaration")
        self._tokenizer.advance()

        # Compile the variable declarations, if there are any
        while ('KEYWORD' == self._tokenizer.token_type()) and \
              (JackKeywords.VAR == self._tokenizer.keyword()):
            self.compile_var_dec()

        # Compile the statements
        self.compile_statements()

        # Add the closing curly brace
        self._validate_symbol(JackSymbols.CLOSING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '}' symbol after subroutine body")
        self._tokenizer.advance()

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        # Expecting the var keyword
        if ('KEYWORD' != self._tokenizer.token_type()) or \
           (JackKeywords.VAR != self._tokenizer.keyword()):
            raise ValueError("CompilationEngine: Expected 'var' keyword for variable declaration")
        self._tokenizer.advance()

        # Add the type
        var_type = self._handle_var_type()
        self._tokenizer.advance()

        # Add the variable names
        self._add_variable_list(VariableKinds.VAR, var_type)

    def compile_statements(self) -> None:
        """
        Compiles a sequence of statements, not including the enclosing 
        curly brackets.
        """
        # Statement is a keyword - Validating it
        while ('KEYWORD' == self._tokenizer.token_type()):
            
            statement = self._tokenizer.keyword()
            if JackKeywords.DO == statement:
                self.compile_do()
            elif JackKeywords.LET == statement:
                self.compile_let()
            elif JackKeywords.WHILE == statement:
                self.compile_while()
            elif JackKeywords.RETURN == statement:
                self.compile_return()
            elif JackKeywords.IF == statement:
                self.compile_if()
            else:
                raise ValueError(f"CompilationEngine: Unexpected keyword {self._tokenizer.keyword()}, expected statement")
        
    def compile_do(self) -> None:
        """Compiles a do statement."""
        # Handling the do keyword itself
        self._validate_keyword(JackKeywords.DO, "CompilationEngine: Expected 'do' keyword")
        self._insert_keyword(JackKeywords.DO)
        self._tokenizer.advance()

        # Handling the first identifier token - it can be a class name, a variable name, or a subroutine name
        self._insert_identifier(self._tokenizer.identifier())
        self._tokenizer.advance()

        # Handling the subrountine call for a case of a class name or a variable name (by ref)
        if ('SYMBOL' == self._tokenizer.token_type()) and \
           (JackSymbols.DOT == self._tokenizer.symbol()):
            self.compile_subroutine_ref_call()

        # Handling the expression list
        self.compile_expression_list()

        # Handling the line terminator
        self._validate_symbol(JackSymbols.LINE_TERMINATOR, 
                              "CompilationEngine: Expected ';' symbol after subroutine call")
        self._insert_symbol(JackSymbols.LINE_TERMINATOR)
        self._tokenizer.advance()

    def compile_let(self) -> None:
        """Compiles a let statement."""
        
        # Handling the let keyword itself
        self._validate_keyword(JackKeywords.LET, "CompilationEngine: Expected 'let' keyword")
        self._tokenizer.advance()

        # Parsing the variable name and retrieving it from the symbol table
        var_symbol = self._symbol_table[self._tokenizer.identifier()]
        self._tokenizer.advance()

        # Making sure a symbol appears after the variable name, since it must be
        # either equal sign or the beginning of array access expression
        if 'SYMBOL' == self._tokenizer.token_type():
            if JackSymbols.OPENING_SQUARE_BRACKET == self._tokenizer.symbol():
                if 'Array' != var_symbol.type():
                    raise ValueError("CompilationEngine: Array access is only allowed for array variables")
                self._handle_array_access()
            elif JackSymbols.EQUALS != self._tokenizer.symbol(): # It's not a [ nor =
                raise ValueError(f"CompilationEngine: Expected [ or =, got {self._tokenizer.symbol()}")
            
        # Handling the equal sign - it must appear either way
        self._validate_symbol(JackSymbols.EQUALS, 
                              f"CompilationEngine: Expected '=' symbol after variable name, got {self._tokenizer.symbol()}")
        self._tokenizer.advance()
        
        # Handling the expression, we will not validate whether the expression's
        # output type is the same as the variable's type, as Jack is defined as weakly typed
        self.compile_expression()

        # At this stage we expect that the stack topmost value is the value to be assigned
        self._vm_assign_variable_value(var_symbol)

        # Handling the line terminator
        self._validate_symbol(JackSymbols.LINE_TERMINATOR, "CompilationEngine: Expected line termination")
        self._insert_symbol(self._tokenizer.symbol())
        self._tokenizer.advance()

    def compile_while(self) -> None:
        """Compiles a while statement."""
        # Handling the while keyword itself
        self._validate_keyword(JackKeywords.WHILE, "CompilationEngine: Expected 'while' keyword")
        self._insert_keyword(JackKeywords.WHILE)
        self._tokenizer.advance()

        # Handling the opening round bracket
        self._validate_symbol(JackSymbols.OPENING_PARENTHESIS, 
                              "CompilationEngine: Expected '(' symbol after while keyword")
        self._insert_symbol(JackSymbols.OPENING_PARENTHESIS)
        self._tokenizer.advance()

        # Handling the expression
        self.compile_expression()

        # Handling the closing round bracket
        self._validate_symbol(JackSymbols.CLOSING_PARENTHESIS, 
                              "CompilationEngine: Expected ')' symbol after expression")
        self._insert_symbol(JackSymbols.CLOSING_PARENTHESIS)
        self._tokenizer.advance()
        
        # Handling the opening curly brace
        self._validate_symbol(JackSymbols.OPENING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '{' symbol after while expression")
        self._insert_symbol(JackSymbols.OPENING_CURLY_BRACKET)
        self._tokenizer.advance()

        # Handling the statements
        self.compile_statements()

        # Handling the closing curly brace
        self._validate_symbol(JackSymbols.CLOSING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '}' symbol after while statements")
        self._insert_symbol(JackSymbols.CLOSING_CURLY_BRACKET)
        self._tokenizer.advance()

    def compile_return(self) -> None:
        """Compiles a return statement."""
        # Handling the return keyword itself
        self._validate_keyword(JackKeywords.RETURN, "CompilationEngine: Expected 'return' keyword")
        self._insert_keyword(JackKeywords.RETURN)
        self._tokenizer.advance()

        # Handling the expression
        if ('SYMBOL' != self._tokenizer.token_type()) or \
           (JackSymbols.LINE_TERMINATOR != self._tokenizer.symbol()):
            self.compile_expression()

        # Handling the line terminator
        self._validate_symbol(JackSymbols.LINE_TERMINATOR, "CompilationEngine: Expected line termination")
        self._insert_symbol(self._tokenizer.symbol())
        self._tokenizer.advance()

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        # Handling the if keyword itself
        self._validate_keyword(JackKeywords.IF, "CompilationEngine: Expected 'if' keyword")
        self._insert_keyword(JackKeywords.IF)
        self._tokenizer.advance()

        # Handling the opening round bracket
        self._validate_symbol(JackSymbols.OPENING_PARENTHESIS, 
                              "CompilationEngine: Expected '(' symbol after if keyword")
        self._insert_symbol(JackSymbols.OPENING_PARENTHESIS)
        self._tokenizer.advance()

        # Handling the expression
        self.compile_expression()

        # Handling the closing round bracket
        self._validate_symbol(JackSymbols.CLOSING_PARENTHESIS, 
                              "CompilationEngine: Expected ')' symbol after expression")
        self._insert_symbol(JackSymbols.CLOSING_PARENTHESIS)
        self._tokenizer.advance()

        # Handling the opening curly brace
        self._validate_symbol(JackSymbols.OPENING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '{' symbol after if expression")
        self._insert_symbol(JackSymbols.OPENING_CURLY_BRACKET)
        self._tokenizer.advance()

        # Handling the statements
        self.compile_statements()

        # Handling the closing curly brace
        self._validate_symbol(JackSymbols.CLOSING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '}' symbol after if statements")
        self._insert_symbol(JackSymbols.CLOSING_CURLY_BRACKET)
        self._tokenizer.advance()
        
        # Handling the possibility of an else clause
        if ('KEYWORD' == self._tokenizer.token_type()) and \
           (JackKeywords.ELSE == self._tokenizer.keyword()):
            self._insert_keyword(JackKeywords.ELSE)
            self._tokenizer.advance()

            # Handling the opening curly brace
            self._validate_symbol(JackSymbols.OPENING_CURLY_BRACKET, 
                                  "CompilationEngine: Expected '{' symbol after else keyword")
            self._insert_symbol(JackSymbols.OPENING_CURLY_BRACKET)
            self._tokenizer.advance()

            # Handling the statements
            self.compile_statements()

            # Handling the closing curly brace
            self._validate_symbol(JackSymbols.CLOSING_CURLY_BRACKET, 
                                  "CompilationEngine: Expected '}' symbol after else statements")
            self._insert_symbol(JackSymbols.CLOSING_CURLY_BRACKET)
            self._tokenizer.advance()

    def compile_expression(self) -> None:
        """Compiles an expression."""
        self.compile_term()
        # Compiling more terms if and only if there are expression operators
        while ('SYMBOL' == self._tokenizer.token_type()) and \
              (self._tokenizer.symbol() in CompilationEngine.JACK_EXPRESSION_OPS):
            self._insert_symbol(self._tokenizer.symbol())
            self._tokenizer.advance()
            self.compile_term()

    def compile_term(self) -> None:
        """Compiles a term. 
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        token_type = self._tokenizer.token_type()
        if 'INT_CONST' == token_type:
            self.compile_integer_constant_term()
        elif 'STRING_CONST' == token_type:
            self.compile_string_constant_term()
        elif 'KEYWORD' == token_type:
            self.compile_keyword_term()
        elif 'IDENTIFIER' == token_type:
            self.compile_identifier_term()
        elif 'SYMBOL' == token_type:
            self.compile_symbol_term()      
        else:
            raise ValueError(f"CompilationEngine: Unexpected token type {token_type}")

    def compile_identifier_term(self) -> None:
        """
        Compiles an identifier term - A variable, an array entry, or a subroutine call.
        """
        # Handling the name - It MUST appear! Otherwise we got here in mysterious ways.
        self._insert_identifier(self._tokenizer.identifier())
        self._tokenizer.advance()

        # Handling the possibility of an array access
        if ('SYMBOL' == self._tokenizer.token_type()) and \
           (JackSymbols.OPENING_SQUARE_BRACKET == self._tokenizer.symbol()):
            self._handle_array_access()

        # Handling the possibility of a subroutine call
        elif ('SYMBOL' == self._tokenizer.token_type()) and \
             (JackSymbols.OPENING_PARENTHESIS == self._tokenizer.symbol()):
            self.compile_expression_list()

        # Handling the possibility of a subroutine call for a class name or a variable name
        elif ('SYMBOL' == self._tokenizer.token_type()) and \
             (JackSymbols.DOT == self._tokenizer.symbol()):
            self.compile_subroutine_ref_call()
            self.compile_expression_list()
        else:
            # If it's not an array access or a subroutine call, then it's a variable,
            # nothing should happen in this case
            pass

    def compile_integer_constant_term(self) -> None:
        """Compiles an integer constant term."""
        int_val = self._tokenizer.int_val()
        if HACK_MIN_INT > int_val or HACK_MAX_INT < int_val:
            raise ValueError(f"CompilationEngine: Integer constant out of range: {int_val}")
        self._vm_writer.write_push(VMMemorySegments.CONST, int_val)
        self._tokenizer.advance()

    def compile_string_constant_term(self) -> None:
        """Compiles a string constant term."""
        string_val = self._tokenizer.string_val()
        self._os_api.new_string(string_val)
        self._tokenizer.advance()

    def compile_keyword_term(self) -> None:
        """Compiles a keyword constant term."""
        self._insert_keyword(self._tokenizer.keyword())
        self._tokenizer.advance()

    def compile_symbol_term(self) -> None:
        """Compiles a symbol term."""
        # Handling a nested expression
        if JackSymbols.OPENING_PARENTHESIS == self._tokenizer.symbol():
            self._insert_symbol(JackSymbols.OPENING_PARENTHESIS)
            self._tokenizer.advance()

            self.compile_expression()

            self._validate_symbol(JackSymbols.CLOSING_PARENTHESIS, 
                                    "CompilationEngine: Expected ')' symbol after expression")
            self._insert_symbol(JackSymbols.CLOSING_PARENTHESIS)
            self._tokenizer.advance()

        # Handling a unary expression
        elif self._tokenizer.symbol() in CompilationEngine.JACK_UNARY_EXPRESSION_OPS:
            self._insert_symbol(self._tokenizer.symbol())
            self._tokenizer.advance()
            self.compile_term()
        else:
            raise ValueError(f"CompilationEngine: Unexpected symbol {self._tokenizer.symbol()}")

    def compile_subroutine_ref_call(self) -> None:
        """
        Handling the possibility of a subroutine call for a class name or a variable name.
        If it doesn't exist, nothing would happen
        """
        self._insert_symbol(JackSymbols.DOT)
        self._tokenizer.advance()

        self._insert_identifier(self._tokenizer.identifier())
        self._tokenizer.advance()

    def compile_expression_list(self) -> None:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        # Handling the opening round bracket
        self._validate_symbol(JackSymbols.OPENING_PARENTHESIS, 
                              "CompilationEngine: Expected '(' symbol after subroutine name")
        self._insert_symbol(JackSymbols.OPENING_PARENTHESIS)
        self._tokenizer.advance()

        # Handling the expression list, only if there are expressions in it
        if ('SYMBOL' != self._tokenizer.token_type()) or \
           (JackSymbols.CLOSING_PARENTHESIS != self._tokenizer.symbol()):

            # Handling the first expression, then the rest if there are any (separated by commas)
            self.compile_expression()
            while ('SYMBOL' == self._tokenizer.token_type()) and \
                    (JackSymbols.COMMA == self._tokenizer.symbol()):
                self._insert_symbol(JackSymbols.COMMA)
                self._tokenizer.advance()
                self.compile_expression()

        # Handling the closing round bracket
        self._validate_symbol(JackSymbols.CLOSING_PARENTHESIS, 
                              "CompilationEngine: Expected ')' symbol after expression list")
        self._insert_symbol(JackSymbols.CLOSING_PARENTHESIS)
        self._tokenizer.advance()

    def _handle_array_access(self) -> None:
        """
        """
        self._validate_symbol(JackSymbols.OPENING_SQUARE_BRACKET, 
                              f"CompilationEngine: Expected [ symbol after variable name, got {self._tokenizer.symbol()}")
        self._insert_symbol(JackSymbols.OPENING_SQUARE_BRACKET)
        self._tokenizer.advance()

        self.compile_expression()

        self._validate_symbol(JackSymbols.CLOSING_SQUARE_BRACKET, 
                              f"CompilationEngine: Expected ] symbol after expression, got {self._tokenizer.symbol()}")
        self._insert_symbol(JackSymbols.CLOSING_SQUARE_BRACKET)
        self._tokenizer.advance()

    def _validate_symbol(self, symbol: str, err_msg: str) -> None:
        """
        """
        self._type_validator('SYMBOL', self._tokenizer.symbol, symbol, err_msg)

    def _validate_keyword(self, keyword: str, err_msg: str) -> None:
        """
        """
        self._type_validator('KEYWORD', self._tokenizer.keyword, keyword, err_msg)
    
    def _type_validator(self, type: str, type_func, expected_value: str, err_msg: str):
        """
        """
        if (type != self._tokenizer.token_type()) or (type_func() != expected_value):
            raise ValueError(err_msg)

    def _add_variable_list(self, var_kind: str, var_type: str) -> None:
        """
        Adds a list of variable names to the XML.
        The list is expected to be a comma-separated list of identifiers.
        Advancing to the first token after the terminator.
        :param var_kind: The kind of the variable. As defined in VariableKinds.
        :param var_type: The type of the variable. As defined in JackVariableTypes.
        """
        # The first token should be an identifier, not a comma, and nothing else.
        if 'IDENTIFIER' != self._tokenizer.token_type():
            raise ValueError(f"CompilationEngine: Expected identifier, got {self._tokenizer.token_type()}")

        current_token = self._tokenizer.identifier() # Holding variable name
        self._symbol_table.define(current_token, var_type, var_kind)
        previous_token_type = self._tokenizer.token_type()
        self._tokenizer.advance()

        # Run until meeting a line termination
        while JackSymbols.LINE_TERMINATOR != current_token:
            
            current_token_type = self._tokenizer.token_type()

            # Handling comma separation, making sure it exists
            if ('IDENTIFIER' == previous_token_type) and \
               ('SYMBOL' == current_token_type):
                
                current_token = self._tokenizer.symbol() # Should be holding a comma
                if (JackSymbols.COMMA != current_token) and (JackSymbols.LINE_TERMINATOR != current_token):
                    raise ValueError(f"CompilationEngine: Expected , or ; got {current_token}")

            # Handling the variable name
            elif ('SYMBOL' == previous_token_type) and \
                 ('IDENTIFIER' == current_token_type):
                
                current_token = self._tokenizer.identifier() # Holding variable name
                self._symbol_table.define(current_token, var_type, var_kind)
            
            previous_token_type = self._tokenizer.token_type()
            self._tokenizer.advance()

    def _handle_var_type(self, with_void=False) -> str:
        """
        Handles a token that is a valid type (as defined in the Jack Language Grammar).
        Validates the type and adds it to the XML.
        :param with_void: Whether to include the void keyword in the valid types.
        :raises ValueError: If the current token is not a valid type.
        :returns: The type of the variable.
        """
        if self._tokenizer.token_type() not in ['KEYWORD', 'IDENTIFIER']:
            raise ValueError(f"CompilationEngine: Expected keyword or identifier, got {self._tokenizer.token_type()}")
        
        # If it's a keyword, it should be int, char, or boolean (or void if with_void is True)
        if ('KEYWORD' == self._tokenizer.token_type()) and \
           (self._tokenizer.keyword() not in (JackVariableTypes.ALL + ([JackKeywords.VOID] if with_void else []))):
            raise ValueError(f"CompilationEngine: Expected int, char, or boolean for type, got {self._tokenizer.keyword()}")
        
        if 'KEYWORD' == self._tokenizer.token_type():
            return self._tokenizer.keyword()
        else: # It's an identifier - If it isn't then an exception would have been raised by now
            return self._tokenizer.identifier()
        
    def _vm_assign_variable_value(self, var_symbol: Symbol) -> None:
        """
        Assigns the stack topmost value to the variable, according to its kind and index.

        :param var_symbol: The symbol of the variable to assign the value to.
        """
        if var_symbol.kind() in [VariableKinds.STATIC, VariableKinds.FIELD]:
            self._vm_writer.write_pop(
                CompilationEngine.SEGMENT_MAP[var_symbol.kind()], var_symbol.index())
        else:
            self._vm_writer.write_pop(
                CompilationEngine.SEGMENT_MAP[var_symbol.kind()], var_symbol.index())

    def _open_subelement(self, tag: str) -> None:
        pass
    
    def _restore_subelement(self, previous_element) -> None:
        pass

    def _insert_keyword(self, keyword: str) -> None:
        pass
        
    def _insert_symbol(self, symbol: str) -> None:
        pass    

    def _insert_identifier(self, identifier: str) -> None:
        pass

    def _insert_int_const(self, int_const: str) -> None:
        pass
        
    def _insert_string_const(self, string_const: str) -> None:
        pass

    @staticmethod
    def _insert_to_xml(root, tag: str, text: str) -> None:
        pass