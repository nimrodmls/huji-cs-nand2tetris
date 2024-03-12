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
from SymbolTable import Symbol, Subroutine, SymbolTable, VariableKinds
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
            # We assume that the Hack VM has the same ASCII values as the ASCII table
            self._vm_writer.write_push(VMMemorySegments.CONST, ord(char))
            self._vm_writer.write_call('String.appendChar', 2)

    def math_mult(self) -> None:
        """
        Multiplies the top 2 values on the stack.
        The function expects those to already be on the stack.
        """
        self._vm_writer.write_call('Math.multiply', 2)

    def math_div(self) -> None:
        """
        Divides the top 2 values on the stack.
        The function expects those to already be on the stack.
        """
        self._vm_writer.write_call('Math.divide', 2)

    def memory_alloc(self) -> None:
        """
        Allocates memory for a new object.
        The size of the object (i.e. amount of fields) is expected to be on the stack.
        """
        self._vm_writer.write_call('Memory.alloc', 1)

class CompilationEngine:
    """
    Gets input from a JackTokenizer and emits its parsed structure into an output stream.
    """

    # All the statements in the Jack language
    JACK_STATEMENTS = [JackKeywords.DO, JackKeywords.LET, JackKeywords.WHILE, 
                       JackKeywords.RETURN, JackKeywords.IF]
    
    JACK_UNARY_OP_TO_VM_OP = {
        JackSymbols.MINUS: VMArithmeticCommands.NEG,
        JackSymbols.TILDE: VMArithmeticCommands.NOT,
        JackSymbols.SHIFT_LEFT: VMArithmeticCommands.SHIFTLEFT,
        JackSymbols.SHIFT_RIGHT: VMArithmeticCommands.SHIFTRIGHT
    }

    JACK_BINARY_OP_TO_VM_OP = {
        JackSymbols.PLUS: VMArithmeticCommands.ADD,
        JackSymbols.MINUS: VMArithmeticCommands.SUB,
        JackSymbols.AMPERSAND: VMArithmeticCommands.AND,
        JackSymbols.PIPE: VMArithmeticCommands.OR,
        JackSymbols.LESS_THAN: VMArithmeticCommands.LT,
        JackSymbols.GREATER_THAN: VMArithmeticCommands.GT,
        JackSymbols.EQUALS: VMArithmeticCommands.EQ,
        JackSymbols.ASTERISK: None, # Handled separately via OS API
        JackSymbols.SLASH: None # Handled separately via OS API
    }
    
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

        # Saves the current subroutine type depending on the context
        # it is updated when a new subroutine is being compiled and it affects
        # how certain statements within are being compiled
        self._current_subroutine: Subroutine = None
        # Saves all the subroutines in the class, and their types
        self._subroutines = {}
        # Saves the current class name
        self._class_name = None
        # Saves the current if & while count, for unique labels
        self._while_count = 0
        self._if_count = 0
        
    def finalize(self):
        self._symbol_table.print_class_symbols()

    def compile_class(self) -> None:
        """
        Compiles a complete class
        """
        if ('KEYWORD' != self._tokenizer.token_type()) or (JackKeywords.CLASS != self._tokenizer.keyword()):
            raise ValueError("CompilationEngine: Expected 'class' keyword")
        self._tokenizer.advance()

        # Add the class name
        self._class_name = self._tokenizer.identifier()
        self._tokenizer.advance()

        # Expecting the opening curly brace
        open_curly = self._tokenizer.symbol()
        if JackSymbols.OPENING_CURLY_BRACKET != open_curly:
            raise ValueError("CompilationEngine: Expected '{' symbol after class ID")
        self._tokenizer.advance()

        # Compile the class variables
        while ('KEYWORD' == self._tokenizer.token_type()) and \
              (self._tokenizer.keyword() in [JackKeywords.STATIC, JackKeywords.FIELD]):
            self.compile_class_var_dec()

        # Compile the subroutines
        while ('KEYWORD' == self._tokenizer.token_type()) and \
              (self._tokenizer.keyword() in [JackKeywords.CONSTRUCTOR, JackKeywords.FUNCTION, JackKeywords.METHOD]):
            self.compile_subroutine()

        # Expecting the closing curly brace
        close_curly = self._tokenizer.symbol()
        if JackSymbols.CLOSING_CURLY_BRACKET != close_curly:
            raise ValueError("CompilationEngine: Expected '}' symbol after class body")
        self._tokenizer.advance()

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        # Expecting the static or field keyword
        if ('KEYWORD' != self._tokenizer.token_type()) or \
           (self._tokenizer.keyword() not in [VariableKinds.STATIC, VariableKinds.FIELD]):
            raise ValueError("CompilationEngine: Expected 'static' or 'field' keyword for class variables")
        
        var_kind = self._tokenizer.keyword()
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
        # Expecting the constructor, function, or method keyword, 
        # and Setting the context accordingly
        subroutine_kind = self._tokenizer.keyword()
        self._tokenizer.advance()

        # Get the return type
        ret_type = self._handle_var_type(with_void=True)
        self._tokenizer.advance()

        # Get the subroutine name
        func_name = self._tokenizer.identifier()
        self._tokenizer.advance()

        self._current_subroutine = Subroutine(func_name, ret_type, subroutine_kind)

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

        # Write the function declaration - At this stage we know how many local
        # variables we have, so it's possible to declare
        self._vm_writer.write_function(
            f"{self._class_name}.{self._current_subroutine.name}", 
            self._symbol_table.var_count(VariableKinds.VAR))
        
        if JackKeywords.METHOD == self._current_subroutine.kind:
            # For methods, the first argument is always 'this'
            self._vm_writer.write_push(VMMemorySegments.ARG, 0)
            self._vm_writer.write_pop(VMMemorySegments.POINTER, 0)
        elif JackKeywords.CONSTRUCTOR == self._current_subroutine.kind:
            # For constructors, we allocate memory for the object
            self._vm_writer.write_push(VMMemorySegments.CONST, 
                                       self._symbol_table.var_count(VariableKinds.FIELD))
            self._os_api.memory_alloc()
            # We set the 'this' pointer according to the returned value of the memory allocation
            self._vm_writer.write_pop(VMMemorySegments.POINTER, 0)

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
        self._tokenizer.advance()

        # Handling the first identifier token - it can be a class name, a variable name, or a subroutine name
        identifier = self._tokenizer.identifier()
        self._tokenizer.advance()

        # Handling the subrountine call for a case of a class name or a variable name (by ref)
        if ('SYMBOL' == self._tokenizer.token_type()) and \
           (JackSymbols.DOT == self._tokenizer.symbol()):
            self.compile_subroutine_ref_call(identifier)
        else: # Otherwise it's a subroutine call implicitly refering to 'this'
            self.compile_subroutine_call(identifier)

        # Getting rid of the return value of the subroutine call
        self._vm_writer.write_pop(VMMemorySegments.TEMP, 0)

        # Handling the line terminator
        self._validate_symbol(JackSymbols.LINE_TERMINATOR, 
                              "CompilationEngine: Expected ';' symbol after subroutine call")
        self._tokenizer.advance()

    def compile_let(self) -> None:
        """Compiles a let statement."""
        
        # Handling the let keyword itself
        self._validate_keyword(JackKeywords.LET, "CompilationEngine: Expected 'let' keyword")
        self._tokenizer.advance()

        # Parsing the variable name and retrieving it from the symbol table
        var_symbol = self._symbol_table[self._tokenizer.identifier()]
        self._tokenizer.advance()

        is_array = False
        # Making sure a symbol appears after the variable name, since it must be
        # either equal sign or the beginning of array access expression
        if 'SYMBOL' == self._tokenizer.token_type():
            if JackSymbols.OPENING_SQUARE_BRACKET == self._tokenizer.symbol():
                if 'Array' != var_symbol.type:
                    raise ValueError("CompilationEngine: Array access is only allowed for array variables")
                is_array = True
                # The expression inside the square brackets is evaluated 
                # and the result is pushed to the top of stack
                self._handle_array_access()
                # Pushing the base address of the array to the stack
                self._vm_writer.write_push(CompilationEngine.SEGMENT_MAP[var_symbol.kind], var_symbol.index)
                # Adding the array base address to the requested index
                self._vm_writer.write_arithmetic(VMArithmeticCommands.ADD)
            elif JackSymbols.EQUALS != self._tokenizer.symbol(): # It's not a [ nor =
                raise ValueError(f"CompilationEngine: Expected [ or =, got {self._tokenizer.symbol()}")
            
        # Handling the equal sign - it must appear either way
        self._validate_symbol(JackSymbols.EQUALS, 
                              f"CompilationEngine: Expected '=' symbol after variable name, got {self._tokenizer.symbol()}")
        self._tokenizer.advance()
        
        # Handling the expression, we will not validate whether the expression's
        # output type is the same as the variable's type, as Jack is defined as weakly typed
        self.compile_expression()

        # Assigning the value to the variable
        if is_array: # If the variable is an array then it receives special treatment
            self._vm_writer.write_pop(VMMemorySegments.TEMP, 0)
            self._vm_writer.write_pop(VMMemorySegments.POINTER, 1)
            self._vm_writer.write_push(VMMemorySegments.TEMP, 0)
            self._vm_writer.write_pop(VMMemorySegments.THAT, 0)
        else:
            # At this stage we expect that the stack topmost value is the value to be assigned
            self._vm_assign_variable_value(var_symbol)

        # Handling the line terminator
        self._validate_symbol(JackSymbols.LINE_TERMINATOR, "CompilationEngine: Expected line termination")
        self._tokenizer.advance()

    def compile_while(self) -> None:
        """Compiles a while statement."""
        # Handling the while keyword itself
        self._validate_keyword(JackKeywords.WHILE, "CompilationEngine: Expected 'while' keyword")
        self._tokenizer.advance()

        # Handling the opening round bracket
        self._validate_symbol(JackSymbols.OPENING_PARENTHESIS, 
                              "CompilationEngine: Expected '(' symbol after while keyword")
        self._tokenizer.advance()

        self._vm_writer.write_label(f"WHILE_EXP{self._while_count}")

        # Handling the expression - The value would be in top of the stack
        self.compile_expression()

        # If the expression is false, we jump to the end of the while loop,
        # otherwise we continue to the statements
        self._vm_writer.write_arithmetic(VMArithmeticCommands.NOT)
        self._vm_writer.write_if_goto(f"WHILE_END{self._while_count}")

        # Handling the closing round bracket
        self._validate_symbol(JackSymbols.CLOSING_PARENTHESIS, 
                              "CompilationEngine: Expected ')' symbol after expression")
        self._tokenizer.advance()
        
        # Handling the opening curly brace
        self._validate_symbol(JackSymbols.OPENING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '{' symbol after while expression")
        self._tokenizer.advance()

        # Handling the statements
        self.compile_statements()

        # Unconditionally jump back to the beginning of the 
        # while expression, to evaluate the expression again
        self._vm_writer.write_goto(f"WHILE_EXP{self._while_count}")
        self._vm_writer.write_label(f"WHILE_END{self._while_count}")

        # Handling the closing curly brace
        self._validate_symbol(JackSymbols.CLOSING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '}' symbol after while statements")
        self._tokenizer.advance()

    def compile_return(self) -> None:
        """Compiles a return statement."""
        # Handling the return keyword itself
        self._validate_keyword(JackKeywords.RETURN, "CompilationEngine: Expected 'return' keyword")
        self._tokenizer.advance()

        # Handling the expression, the result would be in the top of the stack
        if (JackKeywords.VOID == self._current_subroutine.return_type):
            self._vm_writer.write_push(VMMemorySegments.CONST, 0)

        if ('SYMBOL' != self._tokenizer.token_type()) or \
           (JackSymbols.LINE_TERMINATOR != self._tokenizer.symbol()):
            # Void functions should have empty expression, if we reached here it isn't the case
            if (JackKeywords.VOID == self._current_subroutine.return_type):
                raise ValueError("CompilationEngine: Void function cannot return a value")
            # Constructor must return 'this'
            elif ('KEYWORD' == self._tokenizer.token_type()) and \
                 (JackKeywords.THIS != self._tokenizer.keyword()) and \
                 (JackKeywords.CONSTRUCTOR == self._current_subroutine.kind):
                raise ValueError("CompilationEngine: Constructor must return 'this'")
            else: # Otherwise it's good to go
                self.compile_expression()

        # Handling the line terminator
        self._validate_symbol(JackSymbols.LINE_TERMINATOR, "CompilationEngine: Expected line termination")
        self._tokenizer.advance()

        self._vm_writer.write_return()

    def compile_if(self) -> None:
        """
        Compiles a if statement, possibly with a trailing else clause
        """
        # Handling the if keyword itself
        self._validate_keyword(JackKeywords.IF, "CompilationEngine: Expected 'if' keyword")
        self._tokenizer.advance()

        # Handling the opening round bracket
        self._validate_symbol(JackSymbols.OPENING_PARENTHESIS, 
                              "CompilationEngine: Expected '(' symbol after if keyword")
        self._tokenizer.advance()

        # Handling the expression
        self.compile_expression()

        # If the expression is false, we jump to the end of the if statement,
        # otherwise we continue to the statements
        self._vm_writer.write_arithmetic(VMArithmeticCommands.NOT)
        self._vm_writer.write_if_goto(f"IF_FALSE{self._if_count}")

        # Handling the closing round bracket
        self._validate_symbol(JackSymbols.CLOSING_PARENTHESIS, 
                              "CompilationEngine: Expected ')' symbol after expression")
        self._tokenizer.advance()

        # Handling the opening curly brace
        self._validate_symbol(JackSymbols.OPENING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '{' symbol after if expression")
        self._tokenizer.advance()

        # Handling the statements
        self.compile_statements()

        # Handling the closing curly brace
        self._validate_symbol(JackSymbols.CLOSING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '}' symbol after if statements")
        self._tokenizer.advance()
        
        # Handling the possibility of an else clause
        if ('KEYWORD' == self._tokenizer.token_type()) and \
           (JackKeywords.ELSE == self._tokenizer.keyword()):
            self._tokenizer.advance()

            # If we reached here, there is an else clause and the true condition
            # therefore the else should not execute and we jump to the end of the if statement
            self._vm_writer.write_goto(f"IF_END{self._if_count}")

            # If there is an else clause, false condition in the if statement jumps here
            self._vm_writer.write_label(f"IF_FALSE{self._if_count}")

            # Handling the opening curly brace
            self._validate_symbol(JackSymbols.OPENING_CURLY_BRACKET, 
                                  "CompilationEngine: Expected '{' symbol after else keyword")
            self._tokenizer.advance()

            # Handling the statements
            self.compile_statements()

            # Handling the closing curly brace
            self._validate_symbol(JackSymbols.CLOSING_CURLY_BRACKET, 
                                  "CompilationEngine: Expected '}' symbol after else statements")
            self._tokenizer.advance()

            # Adding the end of the if statement label, for the true condition
            self._vm_writer.write_label(f"IF_END{self._if_count}")
        else:
            # Otherwise a else clause doesn't exist, and the false condition jumps here,
            # to the end of the if statement
            self._vm_writer.write_label(f"IF_FALSE{self._if_count}")


    def compile_expression(self) -> None:
        """Compiles an expression."""
        self.compile_term()
        # Compiling more terms if and only if there are expression operators
        while ('SYMBOL' == self._tokenizer.token_type()) and \
              (self._tokenizer.symbol() in CompilationEngine.JACK_BINARY_OP_TO_VM_OP.keys()):
            op_symbol = self._tokenizer.symbol()
            self._tokenizer.advance()
            self.compile_term()
            # At this stage, the 2 topmost values in the stack are the values to be operated on
            self._compile_binary_vm_arithmetic(op_symbol)

    def compile_term(self) -> None:
        """
        Compiles a term. 
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.

        The result of the term is expected appear at the top of the stack once
        the routine is done.
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
        identifier = self._tokenizer.identifier()
        self._tokenizer.advance()

        # Handling the possibility of an array access
        if ('SYMBOL' == self._tokenizer.token_type()) and \
           (JackSymbols.OPENING_SQUARE_BRACKET == self._tokenizer.symbol()):
            # The expression inside the square brackets is evaluated 
            # and the result is pushed to the top of stack
            self._handle_array_access()
            # Adding the array base address to the requested index
            var = self._symbol_table[identifier]
            self._vm_writer.write_push(CompilationEngine.SEGMENT_MAP[var.kind], var.index)
            self._vm_writer.write_arithmetic(VMArithmeticCommands.ADD)
            # Placing the value of the array entry at the top of the stack
            self._vm_writer.write_pop(VMMemorySegments.POINTER, 1)
            self._vm_writer.write_push(VMMemorySegments.THAT, 0)

        # Handling the possibility of a subroutine call - To the current class,
        # access to 'this' is added implicitly
        elif ('SYMBOL' == self._tokenizer.token_type()) and \
             (JackSymbols.OPENING_PARENTHESIS == self._tokenizer.symbol()):
            self.compile_subroutine_call(identifier)

        # Handling the possibility of a subroutine call for a class name or a variable name
        elif ('SYMBOL' == self._tokenizer.token_type()) and \
             (JackSymbols.DOT == self._tokenizer.symbol()):
            self.compile_subroutine_ref_call(identifier)

        else:
            # If it's not an array access or a subroutine call, then it's a variable. 
            # We find it in memory and push it to the top of the stack.
            var = self._symbol_table[identifier]
            self._vm_writer.write_push(CompilationEngine.SEGMENT_MAP[var.kind], var.index)

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
        """
        Compiles a keyword constant term
        Only the constants true, false, null, and this are accepted.
        """
        keyword = self._tokenizer.keyword()
        # TODO: Add to Unit 7
        # if keyword not in [JackKeywords.TRUE, JackKeywords.FALSE, JackKeywords.NULL, JackKeywords.THIS]:
        #     raise ValueError(f"CompilationEngine: Unexpected keyword in term - {keyword}")
        if JackKeywords.TRUE == keyword:
            self._vm_writer.write_push(VMMemorySegments.CONST, 1)
            self._vm_writer.write_arithmetic(VMArithmeticCommands.NEG)
        elif JackKeywords.FALSE == keyword:
            self._vm_writer.write_push(VMMemorySegments.CONST, 0)
        elif JackKeywords.NULL == keyword:
            self._vm_writer.write_push(VMMemorySegments.CONST, 0)
        elif JackKeywords.THIS == keyword:
            self._vm_writer.write_push(VMMemorySegments.POINTER, 0)
        else:
            raise ValueError(f"CompilationEngine: Unexpected keyword in term - {keyword}")
        self._tokenizer.advance()

    def compile_symbol_term(self) -> None:
        """Compiles a symbol term."""
        # Handling a nested expression
        if JackSymbols.OPENING_PARENTHESIS == self._tokenizer.symbol():
            self._tokenizer.advance() # Advancing past the opening parenthesis

            self.compile_expression()

            self._validate_symbol(JackSymbols.CLOSING_PARENTHESIS, 
                                    "CompilationEngine: Expected ')' symbol after expression")
            self._tokenizer.advance()

        # Handling a unary expression
        elif self._tokenizer.symbol() in CompilationEngine.JACK_UNARY_OP_TO_VM_OP.keys():
            unary_op = self._tokenizer.symbol()
            self._tokenizer.advance()
            self.compile_term()
            # At this stage, the topmost value in the stack is the value to be operated on
            self._compile_unary_vm_arithmetic(unary_op)
        else:
            raise ValueError(f"CompilationEngine: Unexpected symbol {self._tokenizer.symbol()}")

    def compile_subroutine_call(self, subroutine_name: str) -> None:
        """
        Compile subroutine call implicitly refering to 'this'
        """
        # If we are currently compiling a static function, we cannot call a method
        # and all static functions should implicitly be called by ref to the class
        if JackKeywords.FUNCTION == self._current_subroutine.kind:
            raise ValueError("CompilationEngine: Attempted method call in a static function context")
        # TODO: Edge case of calling ctor from a method
            
        # Adding all parameters and the implicit 'this' argument to the stack
        self._vm_writer.write_push(VMMemorySegments.POINTER, 0)
        param_count = self.compile_expression_list()
        # Calling the method, with the implicit 'this' argument (thus adding 1)
        self._vm_writer.write_call(subroutine_name, param_count + 1)

    def compile_subroutine_ref_call(self, ref: str) -> None:
        """
        Handling the possibility of a subroutine call for a class name or a variable name.

        :param ref: The reference to the class or the variable name
        """
        self._tokenizer.advance() # Expecting the dot symbol

        # Handling the subroutine name
        subroutine_name = self._tokenizer.identifier()
        self._tokenizer.advance()

        # TODO: Edge case of nonexisting method, function or ctor

        param_count = 0
        try:
            # If the variable is in the symbol table, then ref is a variable name
            var = self._symbol_table[ref]
            subroutine_name = f"{var.type}.{subroutine_name}"
            # Adding the implicit 'this' argument - Retrieving the variable's address
            # and pushing it to the stack as the first parameter
            param_count += 1
            self._vm_writer.write_push(CompilationEngine.SEGMENT_MAP[var.kind], var.index)
        except ValueError:
            # If the variable is not in the symbol table, then it's a class name
            # we don't check if that class really exists, it should be checked by some sort of a linker
            subroutine_name = f"{ref}.{subroutine_name}"            

        param_count += self.compile_expression_list()
        self._vm_writer.write_call(subroutine_name, param_count)
        return subroutine_name

    def compile_expression_list(self) -> None:
        """
        Compiles a (possibly empty) comma-separated list of expressions

        :returns: The number of expressions in the list
        """
        # Handling the opening round bracket
        self._validate_symbol(JackSymbols.OPENING_PARENTHESIS, 
                              "CompilationEngine: Expected '(' symbol after subroutine name")
        self._tokenizer.advance()

        expression_count = 0
        # Handling the expression list, only if there are expressions in it
        if ('SYMBOL' != self._tokenizer.token_type()) or \
           (JackSymbols.CLOSING_PARENTHESIS != self._tokenizer.symbol()):

            # Handling the first expression, then the rest if there are any (separated by commas)
            self.compile_expression()
            expression_count += 1
            while ('SYMBOL' == self._tokenizer.token_type()) and \
                  (JackSymbols.COMMA == self._tokenizer.symbol()):
                self._tokenizer.advance() # Advancing past the comma
                self.compile_expression()
                expression_count += 1

        # Handling the closing round bracket
        self._validate_symbol(JackSymbols.CLOSING_PARENTHESIS, 
                              "CompilationEngine: Expected ')' symbol after expression list")
        self._tokenizer.advance()

        return expression_count

    def _handle_array_access(self) -> None:
        """
        """
        self._validate_symbol(JackSymbols.OPENING_SQUARE_BRACKET, 
                              f"CompilationEngine: Expected [ symbol after variable name, got {self._tokenizer.symbol()}")
        self._tokenizer.advance()

        self.compile_expression()

        self._validate_symbol(JackSymbols.CLOSING_SQUARE_BRACKET, 
                              f"CompilationEngine: Expected ] symbol after expression, got {self._tokenizer.symbol()}")
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
        Adds a list of variable names to the symbol table.
        The list is expected to be a comma-separated list of identifiers.
        Advancing to the first token after the terminator
        .
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
        if var_symbol.kind in [VariableKinds.STATIC, VariableKinds.FIELD]:
            self._vm_writer.write_pop(
                CompilationEngine.SEGMENT_MAP[var_symbol.kind], var_symbol.index)
        else:
            self._vm_writer.write_pop(
                CompilationEngine.SEGMENT_MAP[var_symbol.kind], var_symbol.index)
            
    def _compile_binary_vm_arithmetic(self, op: str) -> None:
        """
        Compiles a VM arithmetic command. The values to be operated on are expected to be
        at the top of the stack once the routine is called.
        Negation is not handled here - Should be handled separately.
        """
        # Order is important since multiplication and division get special treatment
        if JackSymbols.ASTERISK == op: # Multiplication
            self._os_api.math_mult()
        elif JackSymbols.SLASH == op: # Division
            self._os_api.math_div()
        elif (op in CompilationEngine.JACK_BINARY_OP_TO_VM_OP) and \
             (CompilationEngine.JACK_BINARY_OP_TO_VM_OP[op] is not None):
            self._vm_writer.write_arithmetic(CompilationEngine.JACK_BINARY_OP_TO_VM_OP[op])
        else:
            raise ValueError(f"CompilationEngine: Unexpected binary operator {op}")

    def _compile_unary_vm_arithmetic(self, op: str) -> None:
        """
        Compiles a VM arithmetic command. The value to be operated on is expected to be
        at the top of the stack once the routine is called.
        """
        if op in CompilationEngine.JACK_UNARY_OP_TO_VM_OP:
            self._vm_writer.write_arithmetic(CompilationEngine.JACK_UNARY_OP_TO_VM_OP[op])
        else:
            raise ValueError(f"CompilationEngine: Unexpected unary operator {op}")
