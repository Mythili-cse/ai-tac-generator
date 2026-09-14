"""
TAC Validator Module for AI-Driven Three-Address Code Generator.
Verifies structural correctness, temporary register sequencing, operand/operator validity,
parentheses balance, and final assignment validity of TAC instructions.
"""

from typing import List, Dict, Any
from tac_generator import TACInstruction
from lexer import Token, TOKEN_LPAREN, TOKEN_RPAREN, TOKEN_IDENTIFIER, TOKEN_PLUS, TOKEN_MINUS, TOKEN_MULTIPLY, TOKEN_DIVIDE


class TACValidator:
    """Validates TAC code quality, sequence, and structure."""

    @staticmethod
    def validate(instructions: List[TACInstruction], target_variable: str, tokens: List[Token]) -> Dict[str, Any]:
        """
        Run verification suite on generated TAC instructions.
        Returns dict with check details and pass/fail status.
        """
        checks = []
        all_passed = True

        if not instructions:
            return {
                "passed": False,
                "checks": [{"name": "Empty TAC Check", "status": "FAILED", "detail": "No TAC instructions were generated."}],
                "summary": "Validation failed: TAC instruction list is empty."
            }

        # Check 1: Valid TAC Instruction Format
        format_valid = True
        invalid_detail = ""
        for i, instr in enumerate(instructions):
            if not instr.target or not instr.arg1:
                format_valid = False
                invalid_detail = f"Instruction #{i+1} ('{instr.to_string()}') missing target or primary argument."
                break
            if instr.op and not instr.arg2:
                format_valid = False
                invalid_detail = f"Instruction #{i+1} ('{instr.to_string()}') has operator '{instr.op}' but missing second argument."
                break

        checks.append({
            "name": "Valid TAC Instruction Format",
            "status": "PASSED" if format_valid else "FAILED",
            "detail": f"All {len(instructions)} instruction(s) follow valid Three-Address Code schema." if format_valid else invalid_detail
        })
        if not format_valid: all_passed = False

        # Check 2: Temporary Register Sequence
        temps = [instr.target for instr in instructions if instr.target.startswith('t') and instr.target[1:].isdigit()]
        temp_seq_valid = True
        seq_detail = ""
        expected_index = 1

        for temp in temps:
            index = int(temp[1:])
            if index != expected_index:
                temp_seq_valid = False
                seq_detail = f"Expected temporary t{expected_index}, but found {temp}."
                break
            expected_index += 1

        checks.append({
            "name": "Temporary Sequence Order",
            "status": "PASSED" if temp_seq_valid else "FAILED",
            "detail": f"Temporary registers ({', '.join(temps) if temps else 'None needed'}) properly allocated in sequence." if temp_seq_valid else seq_detail
        })
        if not temp_seq_valid: all_passed = False

        # Check 3: Operand Validity
        invalid_operands = []
        for instr in instructions:
            for arg in [instr.arg1, instr.arg2]:
                if arg and not (arg.isalnum() or arg.startswith('t') or '_' in arg):
                    invalid_operands.append(arg)

        operands_valid = len(invalid_operands) == 0
        checks.append({
            "name": "Operand Validity Check",
            "status": "PASSED" if operands_valid else "FAILED",
            "detail": "All instruction operands are valid identifiers/registers." if operands_valid else f"Invalid operands detected: {', '.join(invalid_operands)}"
        })
        if not operands_valid: all_passed = False

        # Check 4: Operator Validity
        valid_ops = {"+", "-", "*", "/", None}
        invalid_operators = [instr.op for instr in instructions if instr.op not in valid_ops]
        operators_valid = len(invalid_operators) == 0
        checks.append({
            "name": "Operator Validity Check",
            "status": "PASSED" if operators_valid else "FAILED",
            "detail": "All arithmetic operators (+, -, *, /) belong to the supported language grammar." if operators_valid else f"Unsupported operators found: {', '.join(invalid_operators)}"
        })
        if not operators_valid: all_passed = False

        # Check 5: Final Assignment Target
        last_instr = instructions[-1]
        final_valid = (last_instr.target == target_variable)
        checks.append({
            "name": "Final Assignment Target Integrity",
            "status": "PASSED" if final_valid else "FAILED",
            "detail": f"Final result correctly assigned to target variable '{target_variable}'." if final_valid else f"Expected assignment to '{target_variable}', found '{last_instr.target}'."
        })
        if not final_valid: all_passed = False

        # Check 6: Parentheses Balance
        lparens = sum(1 for t in tokens if t.type == TOKEN_LPAREN)
        rparens = sum(1 for t in tokens if t.type == TOKEN_RPAREN)
        parens_valid = (lparens == rparens)
        checks.append({
            "name": "Parentheses Balance Verification",
            "status": "PASSED" if parens_valid else "FAILED",
            "detail": f"Parentheses balanced ({lparens} opening, {rparens} closing)." if parens_valid else f"Mismatched parentheses: {lparens} opening vs {rparens} closing."
        })
        if not parens_valid: all_passed = False

        summary = (
            "TAC validation passed completely. All 6 verification checks satisfied."
            if all_passed else
            "TAC validation failed. One or more compiler checks failed."
        )

        return {
            "passed": all_passed,
            "checks": checks,
            "summary": summary
        }
