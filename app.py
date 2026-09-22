"""
Flask Server Application for AI-Driven Three-Address Code Generator.
Exposes REST API endpoints and integrates Google Gemini AI with deterministic Compiler Engine.
"""

import os
import time
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from lexer import Lexer
from parser import Parser, analyze_expression_stats
from tac_generator import TACGenerator, convert_tac_to_representations
from ai_processor import AIProcessor
from validator import TACValidator

load_dotenv(override=True)


app = Flask(__name__)


@app.route("/")
def index():
    """Render main compiler studio interface."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check API endpoint returning compiler and Gemini configuration status."""
    ai_proc = AIProcessor()
    return jsonify({
        "status": "online",
        "compiler_engine": "online",
        "gemini_configured": ai_proc.is_configured(),
        "timestamp": time.time()
    }), 200


@app.route("/api/generate", methods=["POST"])
def generate_tac():
    """
    Primary API endpoint to generate Three-Address Code and query Gemini AI.
    Expects JSON body: { "expression": "x = (a + b) * (c - d)" }
    """
    data = request.get_json(silent=True)
    if not data or "expression" not in data:
        return jsonify({
            "success": False,
            "error": "Invalid payload. 'expression' field is required in JSON body."
        }), 400

    expression = data["expression"].strip()

    if not expression:
        return jsonify({
            "success": False,
            "error": "Expression cannot be empty. Please enter an arithmetic assignment expression."
        }), 400

    start_time = time.time()

    # Stage 1: Lexical Analysis
    lexer = Lexer(expression)
    tokens, lex_err = lexer.tokenize()
    if lex_err:
        return jsonify({
            "success": False,
            "expression": expression,
            "stage": "Lexical Analysis",
            "error": lex_err,
            "ai": {
                "provider": "Google Gemini",
                "status": "not_run",
                "status_label": "Compiler Syntax Error — Gemini Not Called",
                "result": None,
                "error_message": lex_err
            }
        }), 400

    # Stage 2 & 3: Syntax Analysis & AST Construction
    parser = Parser(tokens)
    ast, parse_err = parser.parse()
    if parse_err:
        return jsonify({
            "success": False,
            "expression": expression,
            "tokens": [t.to_dict() for t in tokens],
            "stage": "Syntax Analysis",
            "error": parse_err,
            "ai": {
                "provider": "Google Gemini",
                "status": "not_run",
                "status_label": "Compiler Syntax Error — Gemini Not Called",
                "result": None,
                "error_message": parse_err
            }
        }), 400

    # Calculate syntax & expression statistics
    expr_stats = analyze_expression_stats(tokens, ast)

    # Stage 4: TAC Generation & Intermediate Code Conversion (Compiler Engine)
    generator = TACGenerator()
    instructions, tac_meta = generator.generate(ast)
    tac_strings = [instr.to_string() for instr in instructions]
    tac_dicts = [instr.to_dict() for instr in instructions]

    # Derivation of Quadruples, Triples, and Indirect Triples (Phase II)
    representations = convert_tac_to_representations(instructions)

    # Stage 5: TAC Validation
    validation = TACValidator.validate(instructions, ast.target, tokens)

    # Stage 6: Google Gemini AI Analysis (only called on valid expressions)
    ai_proc = AIProcessor()
    ai_response = ai_proc.analyze(
        expression,
        [t.to_dict() for t in tokens],
        tac_strings,
        expr_stats,
        representations["quadruples"],
        representations["triples"],
        representations["indirect_triples"]
    )

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    return jsonify({
        "success": True,
        "expression": expression,
        "tokens": [t.to_dict() for t in tokens],
        "target_variable": ast.target,
        "syntax_analysis": expr_stats,
        "tac": tac_strings,
        "tac_details": tac_dicts,
        "quadruples": representations["quadruples"],
        "triples": representations["triples"],
        "indirect_triples": representations["indirect_triples"],
        "tac_meta": {
            "execution_time_ms": elapsed_ms,
            "temporary_count": tac_meta["temporary_count"],
            "instruction_count": tac_meta["instruction_count"]
        },
        "validation": validation,
        "ai": ai_response,
        "error": None
    }), 200


@app.route("/api/explain", methods=["POST"])
def explain_tac():
    """
    Endpoint for the 'EXPLAIN WITH AI' button.
    Expects JSON: { "expression": "...", "tac": [...], "syntax_analysis": {...} }
    """
    data = request.get_json(silent=True)
    if not data or "expression" not in data or "tac" not in data:
        return jsonify({"success": False, "error": "Invalid payload."}), 400

    expression = data["expression"].strip()
    tac_lines = data["tac"]
    syntax_analysis = data.get("syntax_analysis", {})
    quadruples = data.get("quadruples")
    triples = data.get("triples")
    indirect_triples = data.get("indirect_triples")

    ai_proc = AIProcessor()
    explanation_res = ai_proc.explain_with_gemini(
        expression,
        tac_lines,
        syntax_analysis,
        quadruples,
        triples,
        indirect_triples
    )

    return jsonify({
        "success": True,
        "expression": expression,
        "ai_explanation": explanation_res
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting AI-Driven Three-Address Code Generator Server on port {port}...")
    app.run(host="127.0.0.1", port=port, debug=True)
