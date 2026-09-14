"""
Syntax Analyzer & Parser for AI-Driven Three-Address Code Generator.
Parses token stream into an AST while enforcing operator precedence and compiler syntax rules.
Provides detailed syntax diagnostics and step-by-step evaluation order tracing.
"""

from typing import List, Tuple, Optional, Dict, Any
from lexer import (
    Token,
    TOKEN_IDENTIFIER,
    TOKEN_ASSIGN,
    TOKEN_PLUS,
    TOKEN_MINUS,
    TOKEN_MULTIPLY,
    TOKEN_DIVIDE,
    TOKEN_LPAREN,
    TOKEN_RPAREN,
)

# AST Node Classes
class ASTNode:
    """Base class for all AST nodes."""
    pass


class VarNode(ASTNode):
    """Represents a variable or numeric constant identifier."""
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"Var({self.name})"


class BinaryOpNode(ASTNode):
    """Represents a binary arithmetic operation (+, -, *, /)."""
    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"BinaryOp('{self.op}', {self.left}, {self.right})"


class AssignmentNode(ASTNode):
    """Represents an assignment expression: target = expr."""
    def __init__(self, target: str, expr: ASTNode):
        self.target = target
        self.expr = expr

    def __repr__(self):
        return f"Assignment('{self.target}', {self.expr})"


class Parser:
    """
    Recursive Descent Parser for arithmetic assignment expressions.
    
    Grammar Rules:
      Assignment -> IDENTIFIER '=' Expr
      Expr       -> Term (( '+' | '-' ) Term)*
      Term       -> Factor (( '*' | '/' ) Factor)*
      Factor     -> IDENTIFIER | '(' Expr ')'
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token: Optional[Token] = self.tokens[0] if tokens else None

    def advance(self):
        """Advance to the next token."""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def parse(self) -> Tuple[Optional[AssignmentNode], str]:
        """
        Main parse method. Parses an assignment expression.
        Returns (ast_node, error_message).
        """
        if not self.tokens:
            return None, "Syntax Error: Empty expression input."

        # Quick check for parentheses balance before parsing
        paren_check = self._check_parentheses_balance()
        if not paren_check["balanced"]:
            return None, paren_check["error"]

        try:
            ast = self.parse_assignment()
            if self.current_token is not None:
                return None, f"Syntax Error: Unexpected token '{self.current_token.value}' at position {self.current_token.position}."
            return ast, ""
        except SyntaxError as se:
            return None, str(se)
        except Exception as e:
            return None, f"Syntax Error: Invalid expression structure ({str(e)})."

    def _check_parentheses_balance(self) -> Dict[str, Any]:
        """Verify parenthesis matching."""
        stack = []
        for tok in self.tokens:
            if tok.type == TOKEN_LPAREN:
                stack.append(tok)
            elif tok.type == TOKEN_RPAREN:
                if not stack:
                    return {"balanced": False, "error": f"Syntax Error: Unexpected closing parenthesis ')' at position {tok.position}."}
                stack.pop()
        if stack:
            unmatched = stack[-1]
            return {"balanced": False, "error": f"Syntax Error: Unbalanced parentheses — Unmatched opening '(' from position {unmatched.position}."}
        return {"balanced": True, "error": ""}

    def parse_assignment(self) -> AssignmentNode:
        """Parse target = Expr."""
        if not self.current_token or self.current_token.type != TOKEN_IDENTIFIER:
            token_val = self.current_token.value if self.current_token else "EOF"
            raise SyntaxError(f"Syntax Error: Expected target variable at left side of assignment, found '{token_val}'.")

        target_name = self.current_token.value
        self.advance()

        if not self.current_token or self.current_token.type != TOKEN_ASSIGN:
            token_val = self.current_token.value if self.current_token else "EOF"
            raise SyntaxError(f"Syntax Error: Expected '=' operator after variable '{target_name}', found '{token_val}'.")

        self.advance()  # consume '='

        if not self.current_token:
            raise SyntaxError(f"Syntax Error: Expected expression after '=' assignment operator.")

        expr_ast = self.parse_expr()
        return AssignmentNode(target_name, expr_ast)

    def parse_expr(self) -> ASTNode:
        """Parse Expr -> Term (( '+' | '-' ) Term)*"""
        if self.current_token and self.current_token.type in (TOKEN_PLUS, TOKEN_MINUS, TOKEN_MULTIPLY, TOKEN_DIVIDE):
            raise SyntaxError(f"Syntax Error: Unexpected operator '{self.current_token.value}' at position {self.current_token.position}. Expected operand.")

        node = self.parse_term()

        while self.current_token and self.current_token.type in (TOKEN_PLUS, TOKEN_MINUS):
            op_token = self.current_token
            self.advance()

            if self.current_token and self.current_token.type in (TOKEN_PLUS, TOKEN_MINUS, TOKEN_MULTIPLY, TOKEN_DIVIDE):
                raise SyntaxError(f"Syntax Error: Unexpected operator '{self.current_token.value}' immediately following '{op_token.value}' at position {self.current_token.position}.")

            right_node = self.parse_term()
            node = BinaryOpNode(op_token.value, node, right_node)

        return node

    def parse_term(self) -> ASTNode:
        """Parse Term -> Factor (( '*' | '/' ) Factor)*"""
        node = self.parse_factor()

        while self.current_token and self.current_token.type in (TOKEN_MULTIPLY, TOKEN_DIVIDE):
            op_token = self.current_token
            self.advance()

            if self.current_token and self.current_token.type in (TOKEN_PLUS, TOKEN_MINUS, TOKEN_MULTIPLY, TOKEN_DIVIDE):
                raise SyntaxError(f"Syntax Error: Unexpected operator '{self.current_token.value}' immediately following '{op_token.value}' at position {self.current_token.position}.")

            right_node = self.parse_factor()
            node = BinaryOpNode(op_token.value, node, right_node)

        return node

    def parse_factor(self) -> ASTNode:
        """Parse Factor -> IDENTIFIER | '(' Expr ')'"""
        token = self.current_token

        if not token:
            raise SyntaxError("Syntax Error: Unexpected end of expression (missing operand or trailing operator).")

        if token.type == TOKEN_IDENTIFIER:
            self.advance()
            return VarNode(token.value)

        elif token.type == TOKEN_LPAREN:
            self.advance()  # consume '('
            if self.current_token and self.current_token.type == TOKEN_RPAREN:
                raise SyntaxError(f"Syntax Error: Empty parentheses '()' found at position {token.position}.")

            node = self.parse_expr()

            if not self.current_token or self.current_token.type != TOKEN_RPAREN:
                raise SyntaxError(f"Syntax Error: Unmatched opening parenthesis '(' from position {token.position}.")

            self.advance()  # consume ')'
            return node

        else:
            raise SyntaxError(f"Syntax Error: Unexpected operator or token '{token.value}' at position {token.position}. Expected variable or operand.")


def analyze_expression_stats(tokens: List[Token], ast: Optional[AssignmentNode]) -> Dict[str, Any]:
    """
    Computes detailed syntax statistics and step-by-step evaluation order.
    """
    operator_count = 0
    operand_count = 0
    lparen_count = 0
    rparen_count = 0

    for tok in tokens:
        if tok.type in (TOKEN_PLUS, TOKEN_MINUS, TOKEN_MULTIPLY, TOKEN_DIVIDE):
            operator_count += 1
        elif tok.type == TOKEN_IDENTIFIER and tok.position > 1:  # exclude target var
            operand_count += 1
        elif tok.type == TOKEN_LPAREN:
            lparen_count += 1
        elif tok.type == TOKEN_RPAREN:
            rparen_count += 1

    balanced = (lparen_count == rparen_count)

    # Trace Evaluation Order from AST
    evaluation_steps = []
    if ast and isinstance(ast, AssignmentNode):
        temp_counter = [1]
        
        def trace_ast(node):
            if isinstance(node, VarNode):
                return node.name
            elif isinstance(node, BinaryOpNode):
                left_str = trace_ast(node.left)
                right_str = trace_ast(node.right)
                t_name = f"t{temp_counter[0]}"
                temp_counter[0] += 1
                evaluation_steps.append(f"{left_str} {node.op} {right_str}")
                return t_name
            return ""

        final_res = trace_ast(ast.expr)
        evaluation_steps.append(f"assign result '{final_res}' to target '{ast.target}'")

    formatted_steps = [f"{i+1}. {step}" for i, step in enumerate(evaluation_steps)]

    return {
        "syntax_status": "VALID" if ast else "INVALID",
        "parentheses_status": "Balanced" if balanced else "Unbalanced",
        "operator_count": operator_count,
        "operand_count": operand_count,
        "assignment_status": "Valid" if ast else "Invalid",
        "precedence_status": "Correct",
        "evaluation_steps": formatted_steps
    }
