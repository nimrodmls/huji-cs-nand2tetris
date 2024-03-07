class JackVariableTypes:
    """
    A class to hold the different types of variables in the Jack language.
    """
    INT = "int"
    CHAR = "char"
    BOOLEAN = "boolean"
    ALL = [INT, CHAR, BOOLEAN]

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