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
    OPENING_ROUND_BRACKET = "("
    CLOSING_ROUND_BRACKET = ")"
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

class JackKeywoards:
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

class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """
    TOKENS_XML_TAG = "tokens"
    KEYWORD_XML_TAG = "keyword"
    SYMBOL_XML_TAG = "symbol"
    IDENTIFIER_XML_TAG = "identifier"
    INT_CONST_XML_TAG = "integerConstant"
    STRING_CONST_XML_TAG = "stringConstant"
    CLASS_VAR_DEC_XML_TAG = "classVarDec"
    CLASS_SUBROUTINE_XML_TAG = "subroutineDec"
    PARAMETER_LIST_XML_TAG = "parameterList"

    def __init__(self, input_stream: JackTokenizer.JackTokenizer, output_stream) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self._tokenizer = input_stream
        self._output_stream = output_stream

        self._xml_toplevel = xml.Element(CompilationEngine.TOKENS_XML_TAG)
        self._xml_current = self._xml_toplevel

    def finalize(self):
        """Writes the XML to the output stream."""
        xml.ElementTree(self._xml_toplevel).write(self._output_stream, pretty_print=True)

    def compile_class(self) -> None:
        """Compiles a complete class."""
        if ('KEYWORD' != self._tokenizer.token_type()) or (JackKeywoards.CLASS != self._tokenizer.keyword()):
            raise ValueError("CompilationEngine: Expected 'class' keyword")
        
        # Create the root element
        self._insert_keyword(JackKeywoards.CLASS)
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
              (self._tokenizer.keyword() in [JackKeywoards.STATIC, JackKeywoards.FIELD]):
            self.compile_class_var_dec()

        # Compile the subroutines
        while ('KEYWORD' == self._tokenizer.token_type()) and \
              (self._tokenizer.keyword() in [JackKeywoards.CONSTRUCTOR, JackKeywoards.FUNCTION, JackKeywoards.METHOD]):
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
        self._validate_type()
        if 'KEYWORD' == self._tokenizer.token_type():
            self._insert_keyword(self._tokenizer.keyword())
        else: # It's an identifier - If it isn't then _validate_type would have raised an exception
            self._insert_identifier(self._tokenizer.identifier())
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
        self._validate_type(with_void=True)
        if 'KEYWORD' == self._tokenizer.token_type():
            self._insert_keyword(self._tokenizer.keyword())
        else: # It's an identifier - If it isn't then _validate_type would have raised an exception
            self._insert_identifier(self._tokenizer.identifier())
        self._tokenizer.advance()

        # Add the subroutine name
        self._insert_identifier(self._tokenizer.identifier())
        self._tokenizer.advance()

        # Add the opening round bracket
        open_round = self._tokenizer.symbol()
        if JackSymbols.OPENING_ROUND_BRACKET != open_round:
            raise ValueError("CompilationEngine: Expected '(' symbol after subroutine name")
        self._insert_symbol(open_round)
        self._tokenizer.advance()

        # Compile the parameter list
        self.compile_parameter_list()

        # Add the closing round bracket
        close_round = self._tokenizer.symbol()
        if JackSymbols.CLOSING_ROUND_BRACKET != close_round:
            raise ValueError("CompilationEngine: Expected ')' symbol after parameter list")
        self._insert_symbol(close_round)
        self._tokenizer.advance()

        # Restore the previous root element
        self._restore_subelement(xml_previous)

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        # Create the root element
        xml_previous = self._open_subelement(CompilationEngine.PARAMETER_LIST_XML_TAG)

        # Restore the previous root element
        self._restore_subelement(xml_previous)

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        # Your code goes here!
        pass

    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        # Your code goes here!
        pass

    def compile_do(self) -> None:
        """Compiles a do statement."""
        # Your code goes here!
        pass

    def compile_let(self) -> None:
        """Compiles a let statement."""
        # Your code goes here!
        pass

    def compile_while(self) -> None:
        """Compiles a while statement."""
        # Your code goes here!
        pass

    def compile_return(self) -> None:
        """Compiles a return statement."""
        # Your code goes here!
        pass

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        # Your code goes here!
        pass

    def compile_expression(self) -> None:
        """Compiles an expression."""
        # Your code goes here!
        pass

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
        # Your code goes here!
        pass

    def compile_expression_list(self) -> None:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        # Your code goes here!
        pass

    def _add_varname_list(self) -> None:
        """
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

    def _validate_type(self, with_void=False) -> None:
        """
        Validates whether the current token is a valid type.
        :param with_void: Whether to include the void keyword in the valid types.
        :raises ValueError: If the current token is not a valid type.
        """
        if self._tokenizer.token_type() not in ['KEYWORD', 'IDENTIFIER']:
            raise ValueError(f"CompilationEngine: Expected keyword or identifier, got {self._tokenizer.token_type()}")
        
        if 'KEYWORD' == self._tokenizer.token_type() and self._tokenizer.keyword() not in [
            JackKeywoards.INT, JackKeywoards.CHAR, JackKeywoards.BOOLEAN] + ([JackKeywoards.VOID] if with_void else []):
            raise ValueError(f"CompilationEngine: Expected int, char, or boolean for type, got {self._tokenizer.keyword()}")
        
        # Otherwise, it's an identifier - It has no further typing

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
            self._xml_current.text = ''
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
            self._xml_current, CompilationEngine.INT_CONST_XML_TAG, int_const)
        
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