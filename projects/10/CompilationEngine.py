"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
import JackTokenizer
import lxml.etree as xml

class JackSymbols:
    """
    """
    OPENING_CURLY_BRACKET = "{"
    CLOSING_CURLY_BRACKET = "}"
    OPENING_PARENTHESIS = "("
    CLOSING_PARENTHESIS = ")"
    OPENING_SQUARE_BRACKET = "["
    CLOSING_SQUARE_BRACKET = "]"
    DOT = "."
    COMMA = ","
    LINE_TERMINATOR = ";"
    PLUS = "+"
    MINUS = "-"
    ASTERISK = "*"
    SLASH = "/"
    AMPERSAND = "&"
    PIPE = "|"
    LESS_THAN = "<"
    GREATER_THAN = ">"
    EQUALS = "="
    TILDE = "~"
    SHIFT_RIGHT = "#"
    SHIFT_LEFT = "^"
    ALL = [OPENING_CURLY_BRACKET, CLOSING_CURLY_BRACKET, OPENING_PARENTHESIS, CLOSING_PARENTHESIS,
           OPENING_SQUARE_BRACKET, CLOSING_SQUARE_BRACKET, DOT, COMMA, LINE_TERMINATOR, PLUS, MINUS,
           ASTERISK, SLASH, AMPERSAND, PIPE, LESS_THAN, GREATER_THAN, EQUALS, TILDE, SHIFT_RIGHT, SHIFT_LEFT]

class JackKeywords:
    """
    """
    CLASS = "class"
    STATIC = "static"
    FIELD = "field"
    CONSTRUCTOR = "constructor"
    FUNCTION = "function"
    METHOD = "method"
    INT = "int"
    BOOLEAN = "boolean"
    CHAR = "char"
    VOID = "void"
    VAR = "var"
    LET = "let"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    DO = "do"
    RETURN = "return"
    TRUE = "true"
    FALSE = "false"
    NULL = "null"
    THIS = "this"
    ALL = [CLASS, STATIC, FIELD, CONSTRUCTOR, FUNCTION, METHOD, INT, BOOLEAN, CHAR, 
           VOID, VAR, LET, IF, ELSE, WHILE, DO, RETURN, TRUE, FALSE, NULL, THIS]

class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """
    TOKENS_XML_TAG = "tokens"
    CLASS_XML_TAG = "class"
    KEYWORD_XML_TAG = "keyword"
    SYMBOL_XML_TAG = "symbol"
    IDENTIFIER_XML_TAG = "identifier"
    INT_CONST_XML_TAG = "integerConstant"
    STRING_CONST_XML_TAG = "stringConstant"
    CLASS_VAR_DEC_XML_TAG = "classVarDec"
    CLASS_SUBROUTINE_XML_TAG = "subroutineDec"
    PARAMETER_LIST_XML_TAG = "parameterList"
    VAR_DEC_XML_TAG = "varDec"
    STATEMENTS_XML_TAG = "statements"
    CLASS_SUBROUTINE_BODY_XML_TAG = "subroutineBody"
    DO_STATEMENT_XML_TAG = "doStatement"
    LET_STATEMENT_XML_TAG = "letStatement"
    EXPRESSION_LIST_XML_TAG = "expressionList"
    EXPRESSION_XML_TAG = "expression"
    WHILE_STATEMENT_XML_TAG = "whileStatement"
    RETURN_STATEMENT_XML_TAG = "returnStatement"
    IF_STATEMENT_XML_TAG = "ifStatement"
    TERM_XML_TAG = "term"

    JACK_STATEMENTS = [JackKeywords.DO, JackKeywords.LET, JackKeywords.WHILE, 
                       JackKeywords.RETURN, JackKeywords.IF]
    
    JACK_EXPRESSION_OPS = [JackSymbols.PLUS, JackSymbols.MINUS, JackSymbols.ASTERISK,
                            JackSymbols.SLASH, JackSymbols.AMPERSAND, JackSymbols.PIPE,
                            JackSymbols.LESS_THAN, JackSymbols.GREATER_THAN, JackSymbols.EQUALS]
    
    JACK_UNARY_EXPRESSION_OPS = [JackSymbols.MINUS, JackSymbols.TILDE, 
                                 JackSymbols.SHIFT_LEFT, JackSymbols.SHIFT_RIGHT]
    
    MIN_INT = 0
    MAX_INT = 32767

    def __init__(self, input_stream: JackTokenizer.JackTokenizer, output_stream) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self._tokenizer = input_stream
        self._output_stream = output_stream

        self._xml_toplevel = xml.Element(CompilationEngine.CLASS_XML_TAG)
        self._xml_current = self._xml_toplevel

    def finalize(self):
        """Writes the XML to the output stream."""
        xml.ElementTree(self._xml_toplevel).write(self._output_stream, pretty_print=True)

    def compile_class(self) -> None:
        """Compiles a complete class."""
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
        # Create the root element
        xml_previous = self._open_subelement(CompilationEngine.CLASS_VAR_DEC_XML_TAG)

        # Expecting the static or field keyword
        self._insert_keyword(self._tokenizer.keyword())
        self._tokenizer.advance()

        # Add the type
        self._handle_var_type()
        self._tokenizer.advance()

        # Add the variable names
        self._add_varname_list()
        
        # Restore the previous root element
        self._restore_subelement(xml_previous)

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        # Create the root element
        xml_previous = self._open_subelement(CompilationEngine.CLASS_SUBROUTINE_XML_TAG)

        # Expecting the constructor, function, or method keyword
        self._insert_keyword(self._tokenizer.keyword())
        self._tokenizer.advance()

        # Add the return type
        self._handle_var_type(with_void=True)
        self._tokenizer.advance()

        # Add the subroutine name
        self._insert_identifier(self._tokenizer.identifier())
        self._tokenizer.advance()

        # Add the opening round bracket
        open_round = self._tokenizer.symbol()
        self._validate_symbol(open_round, 
                              "CompilationEngine: Expected '(' symbol after subroutine name")
        self._insert_symbol(open_round)
        self._tokenizer.advance()

        # Compile the parameter list
        self.compile_parameter_list()

        # Add the closing round bracket
        close_round = self._tokenizer.symbol()
        self._validate_symbol(close_round, 
                              "CompilationEngine: Expected ')' symbol after parameter list")
        self._insert_symbol(close_round)
        self._tokenizer.advance()

        self.compile_subroutine_body()
        
        # Restore the previous root element
        self._restore_subelement(xml_previous)

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        # Create the root element
        xml_previous = self._open_subelement(CompilationEngine.PARAMETER_LIST_XML_TAG)

        # We expect a closing parenthesis or a comma after the parameter name
        while ('SYMBOL' != self._tokenizer.token_type()) or \
              (JackSymbols.CLOSING_PARENTHESIS != self._tokenizer.symbol()):
            # Handling the parameter type
            self._handle_var_type()
            self._tokenizer.advance()

            # Handling the parameter name
            self._insert_identifier(self._tokenizer.identifier())
            self._tokenizer.advance()

            # Handling the comma
            if JackSymbols.COMMA == self._tokenizer.symbol():
                self._insert_symbol(JackSymbols.COMMA)
                self._tokenizer.advance()

        # Restore the previous root element
        self._restore_subelement(xml_previous)

    def compile_subroutine_body(self) -> None:
        """
        """
        xml_previous = self._open_subelement(CompilationEngine.CLASS_SUBROUTINE_BODY_XML_TAG)

        # Add the opening curly brace
        self._validate_symbol(JackSymbols.OPENING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '{' symbol after subroutine declaration")
        self._insert_symbol(JackSymbols.OPENING_CURLY_BRACKET)
        self._tokenizer.advance()

        # Compile the subroutine body - Variable declarations, and then statements
        while ('KEYWORD' == self._tokenizer.token_type()) and \
              (JackKeywords.VAR == self._tokenizer.keyword()):
            self.compile_var_dec()

        self.compile_statements()

        # Add the closing curly brace
        self._validate_symbol(JackSymbols.CLOSING_CURLY_BRACKET, 
                              "CompilationEngine: Expected '}' symbol after subroutine body")
        self._insert_symbol(JackSymbols.CLOSING_CURLY_BRACKET)
        self._tokenizer.advance()

        # Restore the previous root element
        self._restore_subelement(xml_previous)

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        xml_previous = self._open_subelement(CompilationEngine.VAR_DEC_XML_TAG)

        # Expecting the var keyword
        self._insert_keyword(self._tokenizer.keyword())
        self._tokenizer.advance()

        # Add the type
        self._handle_var_type()
        self._tokenizer.advance()

        # Add the variable names
        self._add_varname_list()

        # Restore the previous root element
        self._restore_subelement(xml_previous)

    def compile_statements(self) -> None:
        """
        Compiles a sequence of statements, not including the enclosing 
        curly brackets.
        """
        xml_previous = self._open_subelement(CompilationEngine.STATEMENTS_XML_TAG)

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
        
        # Restoring the previous root element
        self._restore_subelement(xml_previous)

    def compile_do(self) -> None:
        """Compiles a do statement."""
        # Create the root element
        xml_previous = self._open_subelement(CompilationEngine.DO_STATEMENT_XML_TAG)

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

        # Restoring the previous root element
        self._restore_subelement(xml_previous)

    def compile_let(self) -> None:
        """Compiles a let statement."""
        
        xml_previous = self._open_subelement(CompilationEngine.LET_STATEMENT_XML_TAG)

        # Handling the let keyword itself
        self._validate_keyword(JackKeywords.LET, "CompilationEngine: Expected 'let' keyword")
        self._insert_keyword(JackKeywords.LET)
        self._tokenizer.advance()

        # Handling the variable name
        self._insert_identifier(self._tokenizer.identifier())
        self._tokenizer.advance()

        # Making sure a symbol appears after the variable name, since it must be
        # either equal sign or the beginning of array access expression
        if 'SYMBOL' == self._tokenizer.token_type():
            if JackSymbols.OPENING_SQUARE_BRACKET == self._tokenizer.symbol():
                self._handle_array_access()    
            elif JackSymbols.EQUALS != self._tokenizer.symbol(): # It's not a [ nor =
                raise ValueError(f"CompilationEngine: Expected [ or =, got {self._tokenizer.symbol()}")
            
        # Handling the equal sign - it must appear either way
        self._validate_symbol(JackSymbols.EQUALS, 
                              f"CompilationEngine: Expected '=' symbol after variable name, got {self._tokenizer.symbol()}")
        self._insert_symbol(JackSymbols.EQUALS)
        self._tokenizer.advance()
        
        # Handling the expression
        self.compile_expression()

        # Handling the line terminator
        self._validate_symbol(JackSymbols.LINE_TERMINATOR, "CompilationEngine: Expected line termination")
        self._insert_symbol(self._tokenizer.symbol())
        self._tokenizer.advance()

        # Restoring the previous root element
        self._restore_subelement(xml_previous)

    def compile_while(self) -> None:
        """Compiles a while statement."""
        xml_previous = self._open_subelement(CompilationEngine.WHILE_STATEMENT_XML_TAG)

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

        # Restore the previous root element
        self._restore_subelement(xml_previous)

    def compile_return(self) -> None:
        """Compiles a return statement."""
        xml_previous = self._open_subelement(CompilationEngine.RETURN_STATEMENT_XML_TAG)

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

        # Restore the previous root element
        self._restore_subelement(xml_previous)

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        xml_previous = self._open_subelement(CompilationEngine.IF_STATEMENT_XML_TAG)

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

        # Restore the previous root element
        self._restore_subelement(xml_previous)

    def compile_expression(self) -> None:
        """Compiles an expression."""
        xml_previous = self._open_subelement(CompilationEngine.EXPRESSION_XML_TAG)

        self.compile_term()
        # Compiling more terms if and only if there are expression operators
        while ('SYMBOL' == self._tokenizer.token_type()) and \
              (self._tokenizer.symbol() in CompilationEngine.JACK_EXPRESSION_OPS):
            self._insert_symbol(self._tokenizer.symbol())
            self._tokenizer.advance()
            self.compile_term()

        self._restore_subelement(xml_previous)

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
        xml_previous = self._open_subelement(CompilationEngine.TERM_XML_TAG)

        # PLACEHOLDER for expression-less code
        # self._insert_identifier(self._tokenizer._current_token())
        # self._tokenizer.advance()

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

        # Restoring the previous root element
        self._restore_subelement(xml_previous)

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
        if CompilationEngine.MIN_INT > int_val or CompilationEngine.MAX_INT < int_val:
            raise ValueError(f"CompilationEngine: Integer constant out of range: {int_val}")
        self._insert_int_const(self._tokenizer.int_val())
        self._tokenizer.advance()

    def compile_string_constant_term(self) -> None:
        """Compiles a string constant term."""
        self._insert_string_const(self._tokenizer.string_val())
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

        # As per the XML specification, the expression list subelement is initialized
        # only after the opening round bracket is validated
        xml_previous = self._open_subelement(CompilationEngine.EXPRESSION_LIST_XML_TAG)

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

        self._restore_subelement(xml_previous)

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

    def _add_varname_list(self) -> None:
        """
        Adds a list of variable names to the XML.
        The list is expected to be a comma-separated list of identifiers.
        Advancing to the first token after the terminator.
        """
        # The first token should be an identifier, not a comma, and nothing else.
        if 'IDENTIFIER' != self._tokenizer.token_type():
            raise ValueError(f"CompilationEngine: Expected identifier, got {self._tokenizer.token_type()}")

        current_token = self._tokenizer.identifier()
        previous_token_type = self._tokenizer.token_type()
        self._insert_identifier(current_token)
        self._tokenizer.advance()

        while JackSymbols.LINE_TERMINATOR != current_token:
            
            current_token_type = self._tokenizer.token_type()

            if ('IDENTIFIER' == previous_token_type) and \
               ('SYMBOL' == current_token_type):
                
                current_token = self._tokenizer.symbol()
                if (JackSymbols.COMMA != current_token) and (JackSymbols.LINE_TERMINATOR != current_token):
                    raise ValueError(f"CompilationEngine: Expected , or ; got {current_token}")
                self._insert_symbol(current_token)

            elif ('SYMBOL' == previous_token_type) and \
                 ('IDENTIFIER' == current_token_type):
                
                current_token = self._tokenizer.identifier()
                self._insert_identifier(current_token)
            
            previous_token_type = self._tokenizer.token_type()
            self._tokenizer.advance()

    def _handle_var_type(self, with_void=False) -> None:
        """
        Handles a token that is a valid type (as defined in the Jack Language Grammar).
        Validates the type and adds it to the XML.
        :param with_void: Whether to include the void keyword in the valid types.
        :raises ValueError: If the current token is not a valid type.
        """
        if self._tokenizer.token_type() not in ['KEYWORD', 'IDENTIFIER']:
            raise ValueError(f"CompilationEngine: Expected keyword or identifier, got {self._tokenizer.token_type()}")
        
        # If it's a keyword, it should be int, char, or boolean (or void if with_void is True)
        if 'KEYWORD' == self._tokenizer.token_type() and self._tokenizer.keyword() not in [
            JackKeywords.INT, JackKeywords.CHAR, JackKeywords.BOOLEAN] + ([JackKeywords.VOID] if with_void else []):
            raise ValueError(f"CompilationEngine: Expected int, char, or boolean for type, got {self._tokenizer.keyword()}")
        
        if 'KEYWORD' == self._tokenizer.token_type():
            self._insert_keyword(self._tokenizer.keyword())
        else: # It's an identifier - If it isn't then an exception would have been raised by now
            self._insert_identifier(self._tokenizer.identifier())
        
    def _open_subelement(self, tag: str) -> xml.Element:
        """Opens a subelement in the XML"""
        subelement = xml.Element(tag)
        self._xml_current.append(subelement)

        previous_element = self._xml_current
        self._xml_current = subelement
        return previous_element
    
    def _restore_subelement(self, previous_element: xml.Element) -> None:
        """Restores the previous subelement in the XML"""
        # If the current element is empty, add an empty text to it, 
        # in order to force the enclosing tag to be written
        if 0 == len(self._xml_current):
            # Adding new line messes up the indentation
            self._xml_current.text = '\n'
        self._xml_current = previous_element

    def _insert_keyword(self, keyword: str) -> None:
        """Inserts a keyword into the XML"""
        CompilationEngine._insert_to_xml(
            self._xml_current, CompilationEngine.KEYWORD_XML_TAG, keyword)
        
    def _insert_symbol(self, symbol: str) -> None:
        """Inserts a symbol into the XML"""
        CompilationEngine._insert_to_xml(
            self._xml_current, CompilationEngine.SYMBOL_XML_TAG, symbol)
        
    def _insert_identifier(self, identifier: str) -> None:
        """Inserts an identifier into the XML"""
        CompilationEngine._insert_to_xml(
            self._xml_current, CompilationEngine.IDENTIFIER_XML_TAG, identifier)
        
    def _insert_int_const(self, int_const: str) -> None:
        """Inserts an integer constant into the XML"""
        CompilationEngine._insert_to_xml(
            self._xml_current, CompilationEngine.INT_CONST_XML_TAG, str(int_const))
        
    def _insert_string_const(self, string_const: str) -> None:
        """Inserts a string constant into the XML"""
        CompilationEngine._insert_to_xml(
            self._xml_current, CompilationEngine.STRING_CONST_XML_TAG, string_const)

    @staticmethod
    def _insert_to_xml(root, tag: str, text: str) -> None:
        """Inserts a tag into the XML"""
        tag = xml.Element(tag)
        tag.text = text
        root.append(tag)