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


def convert_tac_to_representations(instructions: List[TACInstruction]) -> Dict[str, Any]:
    """
    Derive Quadruple, Triple, and Indirect Triple intermediate code representations
    dynamically from a list of Three-Address Code instructions.
    """
    quadruples: List[Dict[str, Any]] = []
    triples: List[Dict[str, Any]] = []
    pointer_table: List[Dict[str, Any]] = []
    temp_to_triple_map: Dict[str, str] = {}

    for idx, instr in enumerate(instructions):
        # 1. Quadruple Representation: (op, arg1, arg2, result)
        op_quad = instr.op if instr.op else "="
        arg1_quad = instr.arg1 if instr.arg1 else "-"
        arg2_quad = instr.arg2 if instr.arg2 else "-"
        result_quad = instr.target if instr.target else "-"

        quadruples.append({
            "index": idx,
            "op": op_quad,
            "arg1": arg1_quad,
            "arg2": arg2_quad,
            "result": result_quad
        })

        # 2. Triple Representation: (index, op, arg1, arg2)
        # Substitute temporary variable names (t1, t2) with triple index references e.g. (0), (1)
        arg1_triple = temp_to_triple_map.get(instr.arg1, instr.arg1)
        arg2_triple = temp_to_triple_map.get(instr.arg2, instr.arg2) if instr.arg2 else "-"

        if instr.op:
            op_triple = instr.op
            t_arg1 = arg1_triple
            t_arg2 = arg2_triple
            temp_to_triple_map[instr.target] = f"({idx})"
        else:
            op_triple = "="
            t_arg1 = instr.target
            t_arg2 = arg1_triple

        triple_index_str = f"({idx})"
        triples.append({
            "index": triple_index_str,
            "op": op_triple,
            "arg1": t_arg1,
            "arg2": t_arg2
        })

        # 3. Indirect Triple Representation: Pointer Table + Triples Table
        pointer_table.append({
            "statement_no": idx,
            "pointer": f"P{idx}",
            "triple_ref": f"→ ({idx})"
        })

    return {
        "quadruples": quadruples,
        "triples": triples,
        "indirect_triples": {
            "pointers": pointer_table,
            "triples": triples
        }
    }

