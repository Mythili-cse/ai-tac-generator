"""
Lexical Analyzer (Lexer) for AI-Driven Three-Address Code Generator.
Tokenizes raw expression strings into a stream of structured tokens with categories.
"""

from typing import List, Dict, Any, Tuple

# Token Type Constants
TOKEN_IDENTIFIER = "IDENTIFIER"
TOKEN_ASSIGN = "ASSIGN"
TOKEN_PLUS = "PLUS"
TOKEN_MINUS = "MINUS"
TOKEN_MULTIPLY = "MULTIPLY"
TOKEN_DIVIDE = "DIVIDE"
TOKEN_LPAREN = "LPAREN"
TOKEN_RPAREN = "RPAREN"

# Category Mapping
CATEGORY_IDENTIFIER = "Identifier"
CATEGORY_ASSIGNMENT = "Assignment"
CATEGORY_OPERATOR = "Arithmetic Operator"
CATEGORY_PAREN = "Parenthesis"
CATEGORY_CONSTANT = "Numeric Constant"


class Token:
    """Represents a single lexical token."""

    def __init__(self, type_: str, value: str, position: int, category: str):
        self.type = type_
        self.value = value
        self.position = position
        self.category = category

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "value": self.value,
            "position": self.position,
            "category": self.category
        }

    def __repr__(self) -> str:
        return f"Token({self.type}, '{self.value}', cat='{self.category}', pos={self.position})"


class Lexer:
    """Scans and tokenizes input arithmetic assignment expressions."""

    def __init__(self, expression: str):
        self.expression = expression
        self.position = 0
        self.current_char = self.expression[0] if expression else None

    def advance(self):
        """Advance position pointer in expression."""
        self.position += 1
        if self.position < len(self.expression):
            self.current_char = self.expression[self.position]
        else:
            self.current_char = None

    def tokenize(self) -> Tuple[List[Token], str]:
        """
        Tokenize the input expression.
        Returns (tokens_list, error_message).
        """
        tokens = []

        if not self.expression or not self.expression.strip():
            return [], "Input expression is empty."

        while self.current_char is not None:
            char = self.current_char

            # Skip whitespace
            if char.isspace():
                self.advance()
                continue

            # Identifiers / Variables: [a-zA-Z_][a-zA-Z0-9_]*
            if char.isalpha() or char == '_':
                start_pos = self.position
                ident = ""
                while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
                    ident += self.current_char
                    self.advance()
                tokens.append(Token(TOKEN_IDENTIFIER, ident, start_pos, CATEGORY_IDENTIFIER))
                continue

            # Numeric Constants
            if char.isdigit():
                start_pos = self.position
                num_str = ""
                has_dot = False
                while self.current_char is not None and (self.current_char.isdigit() or (self.current_char == '.' and not has_dot)):
                    if self.current_char == '.':
                        has_dot = True
                    num_str += self.current_char
                    self.advance()
                tokens.append(Token(TOKEN_IDENTIFIER, num_str, start_pos, CATEGORY_CONSTANT))
                continue

            # Operators and Delimiters
            if char == '=':
                tokens.append(Token(TOKEN_ASSIGN, '=', self.position, CATEGORY_ASSIGNMENT))
                self.advance()
            elif char == '+':
                tokens.append(Token(TOKEN_PLUS, '+', self.position, CATEGORY_OPERATOR))
                self.advance()
            elif char == '-':
                tokens.append(Token(TOKEN_MINUS, '-', self.position, CATEGORY_OPERATOR))
                self.advance()
            elif char == '*':
                tokens.append(Token(TOKEN_MULTIPLY, '*', self.position, CATEGORY_OPERATOR))
                self.advance()
            elif char == '/':
                tokens.append(Token(TOKEN_DIVIDE, '/', self.position, CATEGORY_OPERATOR))
                self.advance()
            elif char == '(':
                tokens.append(Token(TOKEN_LPAREN, '(', self.position, CATEGORY_PAREN))
                self.advance()
            elif char == ')':
                tokens.append(Token(TOKEN_RPAREN, ')', self.position, CATEGORY_PAREN))
                self.advance()
            else:
                return [], f"Lexical Error: Unexpected character '{char}' at position {self.position}."

        return tokens, ""
