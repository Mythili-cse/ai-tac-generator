"""
Three-Address Code (TAC) Generator for AI-Driven Three-Address Code Generator.
Traverses the Abstract Syntax Tree (AST) in post-order to produce 3-address instructions.
Provides metadata including temporary count and instruction count.
"""

from typing import List, Dict, Any, Tuple, Optional
from parser import ASTNode, AssignmentNode, BinaryOpNode, VarNode


class TACInstruction:
    """Represents a single Three-Address Code instruction."""

    def __init__(self, line_number: int, target: str, arg1: str, op: Optional[str] = None, arg2: Optional[str] = None):
        self.line_number = line_number
        self.target = target
        self.arg1 = arg1
        self.op = op
        self.arg2 = arg2

    def line_str(self) -> str:
        """Formatted line number prefix (01, 02, ...)."""
        return f"{self.line_number:02d}"

    def to_string(self) -> str:
        """Render standard TAC string representation."""
        if self.op and self.arg2:
            return f"{self.target} = {self.arg1} {self.op} {self.arg2}"
        return f"{self.target} = {self.arg1}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_no": self.line_str(),
            "target": self.target,
            "arg1": self.arg1,
            "op": self.op,
            "arg2": self.arg2,
            "text": self.to_string(),
            "full_line": f"{self.line_str()}  {self.to_string()}"
        }

    def __repr__(self):
        return f"TAC({self.line_str()} {self.to_string()})"


class TACGenerator:
    """Generates Three-Address Code from AST."""

    def __init__(self):
        self.temp_count = 0
        self.line_counter = 0
        self.instructions: List[TACInstruction] = []

    def new_temp(self) -> str:
        """Create next sequential temporary variable (t1, t2, ...)."""
        self.temp_count += 1
        return f"t{self.temp_count}"

    def generate(self, ast: ASTNode) -> Tuple[List[TACInstruction], Dict[str, int]]:
        """
        Generate TAC from given AST root node.
        Returns (instructions_list, metadata_dict).
        """
        self.temp_count = 0
        self.line_counter = 0
        self.instructions = []

        if isinstance(ast, AssignmentNode):
            result_var = self._traverse(ast.expr)
            self.line_counter += 1
            final_instr = TACInstruction(line_number=self.line_counter, target=ast.target, arg1=result_var)
            self.instructions.append(final_instr)
        else:
            self._traverse(ast)

        meta = {
            "temporary_count": self.temp_count,
            "instruction_count": len(self.instructions)
        }

        return self.instructions, meta

    def _traverse(self, node: ASTNode) -> str:
        """Recursively traverse AST nodes and emit instructions."""
        if isinstance(node, VarNode):
            return node.name

        elif isinstance(node, BinaryOpNode):
            left_var = self._traverse(node.left)
            right_var = self._traverse(node.right)
            temp_var = self.new_temp()
            self.line_counter += 1
            
            instr = TACInstruction(line_number=self.line_counter, target=temp_var, arg1=left_var, op=node.op, arg2=right_var)
            self.instructions.append(instr)
            return temp_var

        else:
            raise ValueError(f"Unknown AST node type: {type(node)}")
