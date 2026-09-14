"""
Automated Test Suite for AI-Driven Three-Address Code Generator (Google Gemini Integration).
Verifies Lexer, Parser, TAC Generator, Validator, and Google Gemini AI Processor integration.
"""

import sys
from lexer import Lexer
from parser import Parser, analyze_expression_stats
from tac_generator import TACGenerator
from ai_processor import AIProcessor
from validator import TACValidator


def run_pipeline(expression: str):
    """Run full compiler pipeline on an expression and return results."""
    # Step 1: Lexical Analysis
    lexer = Lexer(expression)
    tokens, lex_err = lexer.tokenize()
    if lex_err:
        return {"success": False, "stage": "Lexical Analysis", "error": lex_err}

    # Step 2: Syntax Analysis
    parser = Parser(tokens)
    ast, parse_err = parser.parse()
    if parse_err:
        return {"success": False, "stage": "Syntax Analysis", "error": parse_err}

    # Step 3: Expression Stats
    stats = analyze_expression_stats(tokens, ast)

    # Step 4: TAC Generation
    generator = TACGenerator()
    instructions, meta = generator.generate(ast)
    tac_strings = [instr.to_string() for instr in instructions]

    # Step 5: Validation
    validation = TACValidator.validate(instructions, ast.target, tokens)

    # Step 6: Google Gemini AI Analysis
    ai = AIProcessor()
    ai_response = ai.analyze(expression, [t.to_dict() for t in tokens], tac_strings, stats)

    return {
        "success": True,
        "expression": expression,
        "tokens": [t.to_dict() for t in tokens],
        "syntax_stats": stats,
        "tac": tac_strings,
        "tac_meta": meta,
        "validation": validation,
        "ai": ai_response
    }


def main():
    print("==================================================")
    print(" RUNNING GOOGLE GEMINI AI COMPILER TEST SUITE")
    print("==================================================\n")

    valid_test_cases = [
        ("Operator Precedence", "a = b + c * d"),
        ("Parentheses Priority", "x = (a + b) * (c - d)"),
        ("Multiple Operators", "result = a + b * c - d"),
        ("Division & Parens", "x = (a + b) * c - d / e")
    ]

    invalid_test_cases = [
        ("Consecutive Operators", "x = a + * b"),
        ("Unbalanced Parentheses", "x = (a + b")
    ]

    passed_count = 0
    total_count = len(valid_test_cases) + len(invalid_test_cases)

    print("--- VALID TEST CASES ---")
    for name, expr in valid_test_cases:
        res = run_pipeline(expr)
        if res["success"] and res["validation"]["passed"]:
            print(f"[PASS] {name}: '{expr}'")
            print(f"       TAC Generated: {res['tac']}")
            print(f"       Gemini AI Status: {res['ai']['status']}")
            passed_count += 1
        else:
            print(f"[FAIL] {name}: '{expr}'")
            print(f"       Error: {res.get('error') or res.get('validation')}")

    print("\n--- INVALID TEST CASES (Should reject before AI call) ---")
    for name, expr in invalid_test_cases:
        res = run_pipeline(expr)
        if not res["success"]:
            print(f"[PASS] {name}: '{expr}' correctly rejected by Compiler Engine.")
            print(f"       Compiler Diagnostic: {res['error']}")
            passed_count += 1
        else:
            print(f"[FAIL] {name}: '{expr}' was expected to fail but succeeded.")

    print(f"\n==================================================")
    print(f" TEST RESULTS: {passed_count}/{total_count} PASSED")
    print(f"==================================================")

    if passed_count != total_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
