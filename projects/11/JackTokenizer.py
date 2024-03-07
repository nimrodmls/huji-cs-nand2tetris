"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import re
import typing
from typing import List


class JackTokenizer:
    """Removes all comments from the input stream and breaks it
    into Jack language tokens, as specified by the Jack grammar.
    
    # Jack Language Grammar

    A Jack file is a stream of characters. If the file represents a
    valid program, it can be tokenized into a stream of valid tokens. The
    tokens may be separated by an arbitrary number of whitespace characters, 
    and comments, which are ignored. There are three possible comment formats: 
    /* comment until closing */ , /** API comment until closing */ , and 
    // comment until the line’s end.

    - ‘xxx’: quotes are used for tokens that appear verbatim (‘terminals’).
    - xxx: regular typeface is used for names of language constructs 
           (‘non-terminals’).
    - (): parentheses are used for grouping of language constructs.
    - x | y: indicates that either x or y can appear.
    - x?: indicates that x appears 0 or 1 times.
    - x*: indicates that x appears 0 or more times.

    ## Lexical Elements

    The Jack language includes five types of terminal elements (tokens).

    - keyword: 'class' | 'constructor' | 'function' | 'method' | 'field' | 
               'static' | 'var' | 'int' | 'char' | 'boolean' | 'void' | 'true' |
               'false' | 'null' | 'this' | 'let' | 'do' | 'if' | 'else' | 
               'while' | 'return'
    - symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
    - integerConstant: A decimal number in the range 0-32767.
    - StringConstant: '"' A sequence of Unicode characters not including 
                      double quote or newline '"' 
    - identifier: A sequence of letters, digits, and underscore ('_') not 
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.

    ## Program Structure

    A Jack program is a collection of classes, each appearing in a separate 
    file. A compilation unit is a single class. A class is a sequence of tokens 
    structured according to the following context free syntax:
    
    - class: 'class' className '{' classVarDec* subroutineDec* '}'
    - classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    - type: 'int' | 'char' | 'boolean' | className
    - subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) 
    - subroutineName '(' parameterList ')' subroutineBody
    - parameterList: ((type varName) (',' type varName)*)?
    - subroutineBody: '{' varDec* statements '}'
    - varDec: 'var' type varName (',' varName)* ';'
    - className: identifier
    - subroutineName: identifier
    - varName: identifier

    ## Statements

    - statements: statement*
    - statement: letStatement | ifStatement | whileStatement | doStatement | 
                 returnStatement
    - letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
    - ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' 
                   statements '}')?
    - whileStatement: 'while' '(' 'expression' ')' '{' statements '}'
    - doStatement: 'do' subroutineCall ';'
    - returnStatement: 'return' expression? ';'

    ## Expressions
    
    - expression: term (op term)*
    - term: integerConstant | stringConstant | keywordConstant | varName | 
            varName '['expression']' | subroutineCall | '(' expression ')' | 
            unaryOp term
    - subroutineCall: subroutineName '(' expressionList ')' | (className | 
                      varName) '.' subroutineName '(' expressionList ')'
    - expressionList: (expression (',' expression)* )?
    - op: '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    - unaryOp: '-' | '~' | '^' | '#'
    - keywordConstant: 'true' | 'false' | 'null' | 'this'
    
    Note that ^, # correspond to shiftleft and shiftright, respectively.
    """
    SYMBOLS = ['{', '}', '(', ')', '[', ']', '.', ',', ';', '+',
               '-', '*', '/', '&', '|', '<', '>', '=', '~', '^', '#']
    
    KEYWORDS = ['class', 'constructor', 'function', 'method', 'field', 
               'static', 'var', 'int', 'char', 'boolean', 'void', 'true',
               'false', 'null', 'this', 'let', 'do', 'if', 'else', 
               'while', 'return']

    def __init__(self, input_stream: typing.TextIO) -> None:
        """Opens the input stream and gets ready to tokenize it.

        Args:
            input_stream (typing.TextIO): input stream.
        """
        raw_code = input_stream.read()

        # Replace all string constants with a unique identifier
        self._string_ids = {}
        strings_pattern = re.compile('\"(.*?)\"')
        for idx, match in enumerate(re.findall(strings_pattern, raw_code)):
            str_id = self._generate_string_uid(idx, raw_code)
            raw_code = raw_code.replace('"'+match+'"', str_id)
            self._string_ids[str_id] = match

        # Remove all comments from the code - Doing this after the string replacement
        # to prevent "comments" being in strings
        raw_code = JackTokenizer._strip_all_comments(raw_code)

        # Split the code into tokens - based on symbols, whitespaces, and string constants
        raw_code = raw_code.split()
        symbols_pattern = re.compile("(" + "|".join(["\\"+sym for sym in JackTokenizer.SYMBOLS]) + ")")
        self._code = []
        for item in raw_code:            
            self._code += [elem for elem in symbols_pattern.split(item) if elem]
        
        self._current_token_idx = 0

    def has_more_tokens(self) -> bool:
        """Do we have more tokens in the input?

        Returns:
            bool: True if there are more tokens, False otherwise.
        """
        return self._current_token_idx < len(self._code) - 1

    def advance(self) -> None:
        """Gets the next token from the input and makes it the current token. 
        This method should be called if has_more_tokens() is true. 
        Initially there is no current token.
        """
        self._current_token_idx += 1

    def token_type(self) -> str:
        """
        Returns:
            str: the type of the current token, can be
            "KEYWORD", "SYMBOL", "IDENTIFIER", "INT_CONST", "STRING_CONST"
        """
        current_token = self._code[self._current_token_idx]
        if current_token in JackTokenizer.KEYWORDS:
            return "KEYWORD"
        if current_token in JackTokenizer.SYMBOLS:
            return "SYMBOL"
        if current_token.isdigit():
            return "INT_CONST"
        if current_token in self._string_ids:
            return "STRING_CONST"
        
        return "IDENTIFIER"

    def keyword(self) -> str:
        """
        Returns:
            str: the keyword which is the current token.
            Should be called only when token_type() is "KEYWORD".
            Can return "CLASS", "METHOD", "FUNCTION", "CONSTRUCTOR", "INT", 
            "BOOLEAN", "CHAR", "VOID", "VAR", "STATIC", "FIELD", "LET", "DO", 
            "IF", "ELSE", "WHILE", "RETURN", "TRUE", "FALSE", "NULL", "THIS"
        """
        if 'KEYWORD' != self.token_type():
            raise ValueError(f"JackTokenizer: Token type is not KEYWORD, it is {self.token_type()}")
        return self._current_token()

    def symbol(self) -> str:
        """
        Returns:
            str: the character which is the current token.
            Should be called only when token_type() is "SYMBOL".
            Recall that symbol was defined in the grammar like so:
            symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
        """
        if 'SYMBOL' != self.token_type():
            raise ValueError(f"JackTokenizer: Token type is not SYMBOL, it is {self.token_type()}")
        return self._current_token()

    def identifier(self) -> str:
        """
        Returns:
            str: the identifier which is the current token.
            Should be called only when token_type() is "IDENTIFIER".
            Recall that identifiers were defined in the grammar like so:
            identifier: A sequence of letters, digits, and underscore ('_') not 
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.
        """
        if 'IDENTIFIER' != self.token_type():
            raise ValueError(f"JackTokenizer: Token type is not IDENTIFIER, it is {self.token_type()}")
        return self._current_token()

    def int_val(self) -> int:
        """
        Returns:
            str: the integer value of the current token.
            Should be called only when token_type() is "INT_CONST".
            Recall that integerConstant was defined in the grammar like so:
            integerConstant: A decimal number in the range 0-32767.
        """
        if 'INT_CONST' != self.token_type():
            raise ValueError(f"JackTokenizer: Token type is not INT_CONST, it is {self.token_type()}")
        return int(self._current_token())

    def string_val(self) -> str:
        """
        Returns:
            str: the string value of the current token, without the double 
            quotes. Should be called only when token_type() is "STRING_CONST".
            Recall that StringConstant was defined in the grammar like so:
            StringConstant: '"' A sequence of Unicode characters not including 
                      double quote or newline '"'
        """
        if 'STRING_CONST' != self.token_type():
            raise ValueError(f"JackTokenizer: Token type is not STRING_CONST, it is {self.token_type()}")
        return self._string_ids[self._current_token()]

    def _current_token(self) -> str:
        """
        :return: The current token in the code.
        """
        return self._code[self._current_token_idx]

    def _generate_string_uid(self, idx: int, raw_code: List[str]) -> str:
        """
        Generates a unique identifier for a string constant.
        Makes sure that the UID doesn't appear in the raw code before 
        assigning it. This is highly unlikely, but still possible.

        :param idx: The index of the string constant.
        :param raw_code: The raw code.
        :return: A unique identifier for the string constant.
        """
        uid = f"STRING_CONST_{idx}"
        while uid in raw_code:
            idx += 1
            uid = f"STRING_CONST_{idx}"
        return uid

    @staticmethod
    def _strip_all_comments(code):
        """
        Removes all comments from the code.
        :param code: The code to remove comments from.
        :return: The code without comments.
        """
        # Regex pattern for /* */ and // comments
        pattern = r"\/\*.*?\*\/|\/\/.*?$"
        code = re.sub(pattern, "", code, flags=re.DOTALL | re.MULTILINE)
        return code
    

if __name__ == "__main__":
    a=JackTokenizer(open("Square\\Main.jack"))
    while a.has_more_tokens():
        print(f"Token type: {a.token_type()}, Token: {a._code[a._current_token_idx]}")
        a.advance()
