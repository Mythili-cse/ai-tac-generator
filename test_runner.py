"""
Automated Test Suite for AI-Driven Three-Address Code Generator (Google Gemini Integration).
Verifies Lexer, Parser, TAC Generator, Validator, and Google Gemini AI Processor integration.
"""

import sys
from lexer import Lexer
from parser import Parser, analyze_expression_stats
from tac_generator import TACGenerator, convert_tac_to_representations
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

    # Step 4: TAC Generation & Intermediate Code Conversion (Phase II)
    generator = TACGenerator()
    instructions, meta = generator.generate(ast)
    tac_strings = [instr.to_string() for instr in instructions]
    reps = convert_tac_to_representations(instructions)

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
        "quadruples": reps["quadruples"],
        "triples": reps["triples"],
        "indirect_triples": reps["indirect_triples"],
        "tac_meta": meta,
        "validation": validation,
        "ai": ai_response
    }


from unittest.mock import patch

def test_quota_exhaustion():
    """Verify that 429 RESOURCE_EXHAUSTED quota error is handled gracefully without affecting compiler TAC engine."""
    proc = AIProcessor()
    proc.api_key = "fake_key_for_quota_test"

    quota_exception = Exception("429 RESOURCE_EXHAUSTED: generate_content_free_tier_requests limit: 20 model: gemini-3.6-flash")

    with patch.object(AIProcessor, '_generate_with_fallback', side_effect=quota_exception):
        res = proc.analyze("x = (a + b) * (c - d)", [], ["t1 = a + b", "t2 = c - d", "t3 = t1 * t2", "x = t3"], {})
        
        assert res["status"] == "quota_exceeded", f"Expected status 'quota_exceeded', got '{res['status']}'"
        assert "quota has been reached" in res["error_message"], "Expected quota error message."
        assert "TAC generation and intermediate-code generation are still available" in res["error_message"], "Expected fallback availability notice."

    print("[PASS] Quota Exhaustion Test: Gemini 429 RESOURCE_EXHAUSTED caught cleanly.")
    print("       User Message:", res["error_message"])


def verify_specific_expressions():
    """Verify exact TAC, Quadruples, Triples, and Indirect Triples output for required expressions."""
    print("--- VERIFYING SPECIFIC COMPILER EXPRESSIONS ---")

    # Expression 1: a = b + c * d
    res1 = run_pipeline("a = b + c * d")
    assert res1["success"], "a = b + c * d parsing failed"
    assert res1["tac"] == ['t1 = c * d', 't2 = b + t1', 'a = t2']
    assert res1["quadruples"][0] == {'index': 0, 'op': '*', 'arg1': 'c', 'arg2': 'd', 'result': 't1'}
    assert res1["quadruples"][1] == {'index': 1, 'op': '+', 'arg1': 'b', 'arg2': 't1', 'result': 't2'}
    assert res1["quadruples"][2] == {'index': 2, 'op': '=', 'arg1': 't2', 'arg2': '-', 'result': 'a'}
    assert res1["triples"][0] == {'index': '(0)', 'op': '*', 'arg1': 'c', 'arg2': 'd'}
    assert res1["triples"][1] == {'index': '(1)', 'op': '+', 'arg1': 'b', 'arg2': '(0)'}
    assert res1["triples"][2] == {'index': '(2)', 'op': '=', 'arg1': 'a', 'arg2': '(1)'}
    assert res1["indirect_triples"]["pointers"][0] == {'statement_no': 0, 'pointer': 'P0', 'triple_ref': '→ (0)'}
    assert res1["indirect_triples"]["pointers"][1] == {'statement_no': 1, 'pointer': 'P1', 'triple_ref': '→ (1)'}
    assert res1["indirect_triples"]["pointers"][2] == {'statement_no': 2, 'pointer': 'P2', 'triple_ref': '→ (2)'}
    print("[PASS] Exact Representation Check 1: 'a = b + c * d'")

    # Expression 2: x = (a + b) * (c - d)
    res2 = run_pipeline("x = (a + b) * (c - d)")
    assert res2["success"], "x = (a + b) * (c - d) parsing failed"
    assert res2["tac"] == ['t1 = a + b', 't2 = c - d', 't3 = t1 * t2', 'x = t3']
    assert res2["triples"][0] == {'index': '(0)', 'op': '+', 'arg1': 'a', 'arg2': 'b'}
    assert res2["triples"][1] == {'index': '(1)', 'op': '-', 'arg1': 'c', 'arg2': 'd'}
    assert res2["triples"][2] == {'index': '(2)', 'op': '*', 'arg1': '(0)', 'arg2': '(1)'}
    assert res2["triples"][3] == {'index': '(3)', 'op': '=', 'arg1': 'x', 'arg2': '(2)'}
    assert res2["indirect_triples"]["pointers"][0] == {'statement_no': 0, 'pointer': 'P0', 'triple_ref': '→ (0)'}
    assert res2["indirect_triples"]["pointers"][1] == {'statement_no': 1, 'pointer': 'P1', 'triple_ref': '→ (1)'}
    assert res2["indirect_triples"]["pointers"][2] == {'statement_no': 2, 'pointer': 'P2', 'triple_ref': '→ (2)'}
    assert res2["indirect_triples"]["pointers"][3] == {'statement_no': 3, 'pointer': 'P3', 'triple_ref': '→ (3)'}
    print("[PASS] Exact Representation Check 2: 'x = (a + b) * (c - d)'")

    # Expression 3: Complex Nested Expression y = (a + b) * c - d / e
    res3 = run_pipeline("y = (a + b) * c - d / e")
    assert res3["success"], "y = (a + b) * c - d / e parsing failed"
    assert res3["tac"] == ['t1 = a + b', 't2 = t1 * c', 't3 = d / e', 't4 = t2 - t3', 'y = t4']
    assert len(res3["quadruples"]) == 5
    assert len(res3["triples"]) == 5
    assert len(res3["indirect_triples"]["pointers"]) == 5
    print("[PASS] Exact Representation Check 3: 'y = (a + b) * c - d / e'")


def main():
    print("==================================================")
    print(" RUNNING PHASE II INTERMEDIATE CODE COMPILER TEST SUITE")
    print("==================================================\n")

    valid_test_cases = [
        ("Simple Assignment", "a = b + c"),
        ("Operator Precedence", "a = b + c * d"),
        ("Parentheses Priority", "x = (a + b) * (c - d)"),
        ("Multiple Operators", "result = a + b * c - d"),
        ("Division & Parens", "x = (a + b) * c - d / e"),
        ("Direct Assignment", "x = a"),
        ("Phase II Expression", "result = (p + q) * (r - s)")
    ]

    invalid_test_cases = [
        ("Consecutive Operators", "x = a + * b"),
        ("Unbalanced Parentheses", "x = (a + b"),
        ("Empty Expression", ""),
        ("Missing Assignment Target", "= a + b")
    ]

    passed_count = 0
    total_count = len(valid_test_cases) + len(invalid_test_cases) + 2  # +2 for quota & specific checks

    print("--- QUOTA EXHAUSTION TEST ---")
    try:
        test_quota_exhaustion()
        passed_count += 1
    except Exception as e:
        print(f"[FAIL] Quota Exhaustion Test Failed: {e}")

    try:
        verify_specific_expressions()
        passed_count += 1
    except Exception as e:
        print(f"[FAIL] Specific Expressions Test Failed: {e}")

    print("\n--- VALID TEST CASES (Verifying TAC, Quadruples, Triples & Indirect Triples) ---")
    for name, expr in valid_test_cases:
        res = run_pipeline(expr)
        if res["success"] and res["validation"]["passed"]:
            quads = res["quadruples"]
            trips = res["triples"]
            ind_trips = res["indirect_triples"]

            if len(quads) > 0 and len(trips) > 0 and len(ind_trips["pointers"]) > 0:
                print(f"[PASS] {name}: '{expr}'")
                print(f"       TAC: {res['tac']}")
                print(f"       Quadruples Count: {len(quads)} | Triples Count: {len(trips)} | Indirect Pointers: {len(ind_trips['pointers'])}")
                passed_count += 1
            else:
                print(f"[FAIL] {name}: Representation tables were empty.")
        else:
            print(f"[FAIL] {name}: '{expr}'")
            print(f"       Error: {res.get('error') or res.get('validation')}")

    print("\n--- INVALID TEST CASES (Should reject cleanly without crashing) ---")
    for name, expr in invalid_test_cases:
        res = run_pipeline(expr)
        if not res["success"]:
            print(f"[PASS] {name}: '{expr}' correctly rejected by Compiler Engine.")
            print(f"       Diagnostic: {res['error']}")
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


