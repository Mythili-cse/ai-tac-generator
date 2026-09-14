# AI-Driven Three-Address Code Generator (Phase II Production Mini Project)

An interactive, production-quality compiler design studio built with Python Flask and a modern web interface. This application demonstrates the complete compiler front-end pipeline (**Lexical Analysis &rarr; Syntax Parsing &rarr; Expression Analysis &rarr; AI-Assisted Processing &rarr; TAC Generation &rarr; Validation &rarr; Output Results Studio**) for arithmetic assignment expressions.

---

## 📌 Problem Statement

In compiler design, intermediate code generation is a critical phase following lexical analysis and syntax parsing. **Three-Address Code (TAC)** simplifies complex nested arithmetic expressions into linear sequences of instructions where each instruction has at most three addresses (operands and target). Manually tracing TAC for complex expressions with operator precedence and nested parentheses can be prone to human error.

This project provides an automated, reliable, web-accessible tool to tokenize expressions, parse syntax trees, perform AI-assisted expression analysis, generate accurate TAC, and validate instruction integrity.

---

## 🎯 Objectives

1. **Automated TAC Generation:** Dynamically generate correct Three-Address Code for valid arithmetic assignment expressions.
2. **Precedence & Operator Handling:** Correctly prioritize parentheses `()`, multiplication `*`, division `/`, addition `+`, and subtraction `-`.
3. **Robust Syntax Parsing:** Enforce formal grammar rules and reject invalid expressions (e.g. `x = a + * b`, `x = (a + b`) gracefully with actionable error messages.
4. **AI-Assisted Processing:** Provide intelligent evaluation insights, operator precedence hierarchy breakdowns, and expression complexity scoring.
5. **TAC Verification & Validation:** Perform structural checks on generated TAC to verify temporary register sequencing (`t1`, `t2`, ...) and final target variable assignment.

---

## 🏗️ System Architecture & Visual Pipeline

The compiler engine follows an 8-stage pipeline:

```
[ 1. INPUT ] ──► [ 2. LEXER ] ──► [ 3. PARSER ] ──► [ 4. ANALYZER ]
                                                            │
                                                            ▼
[ 8. OUTPUT ] ◄── [ 7. VALIDATOR ] ◄── [ 6. TAC GEN ] ◄── [ 5. AI PROCESSOR ]
```

1. **Input Expression:** Raw string input (`x = (a + b) * (c - d)`).
2. **Lexical Analysis (Lexer):** Tokenizes input into typed tokens with position and category classification.
3. **Syntax Analysis (Parser):** Builds recursive-descent Abstract Syntax Tree (AST).
4. **Expression Analyzer:** Calculates operator/operand counts, parenthesis balance, and step-by-step evaluation order.
5. **AI Processor:** Analyzes expression structure via external LLM API (if `.env` configured) or Compiler Fallback engine (`AI unavailable — Compiler fallback active`).
6. **TAC Generator:** Post-order AST traversal generating 2-digit line-numbered 3-address instructions.
7. **TAC Validator:** Verification checklist enforcing 6 compiler integrity rules.
8. **Results Output Studio:** Dark cyber-themed visual interface with interactive code copy, `.tac` file download, and **"Explain with AI"** modal.

---

## ⚙️ AI API Setup & Configuration

The application uses `python-dotenv` to manage environment variables in a `.env` file:

```env
AI_API_KEY=
AI_API_URL=https://api.openai.com/v1/chat/completions
AI_MODEL=gpt-3.5-turbo
PORT=5000
```

### Modes of Operation:
1. **Without API Key (Compiler Fallback Active):**
   - TAC generation, lexing, parsing, and validation run 100% locally using the compiler engine.
   - Status badge explicitly displays: `"AI unavailable — Compiler fallback active"`.
2. **With API Key (AI Analysis Active):**
   - Calls the configured LLM endpoint (`AI_API_URL`) to populate structured AI analysis, recommendations, and deep explanations.
   - Status badge displays: `"AI Analysis Active"`.

---

## 🚀 How to Install & Run

1. **Navigate to the Project Directory:**
   ```powershell
   cd "c:\Users\Mythili L\AI-TAC-Generator"
   ```

2. **Install Dependencies:**
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. **Run the Automated Test Suite:**
   ```powershell
   python test_runner.py
   ```

4. **Launch the Flask Web Server:**
   ```powershell
   python app.py
   ```

5. **Open Web Browser:**
   Navigate to **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Test Results Summary

Ran `python test_runner.py`:

| Test Name | Input Expression | Generated Three-Address Code (TAC) | Result |
| :--- | :--- | :--- | :---: |
| **Basic Addition** | `a = b + c` | `01  t1 = b + c`<br>`02  a = t1` | **PASS** |
| **Operator Precedence** | `a = b + c * d` | `01  t1 = c * d`<br>`02  t2 = b + t1`<br>`03  a = t2` | **PASS** |
| **Parentheses Priority** | `x = (a + b) * (c - d)` | `01  t1 = a + b`<br>`02  t2 = c - d`<br>`03  t3 = t1 * t2`<br>`04  x = t3` | **PASS** |
| **Multiple Operators** | `result = a + b * c - d` | `01  t1 = b * c`<br>`02  t2 = a + t1`<br>`03  t3 = t2 - d`<br>`04  result = t3` | **PASS** |
| **Mixed Parens & Division**| `x = (a + b) * c - d / e` | `01  t1 = a + b`<br>`02  t2 = t1 * c`<br>`03  t3 = d / e`<br>`04  t4 = t2 - t3`<br>`05  x = t4` | **PASS** |
| **Nested Expressions** | `x = ((a + b) * c) - d` | `01  t1 = a + b`<br>`02  t2 = t1 * c`<br>`03  t3 = t2 - d`<br>`04  x = t3` | **PASS** |
| **Division First** | `x = a / b + c * d` | `01  t1 = a / b`<br>`02  t2 = c * d`<br>`03  t3 = t1 + t2`<br>`04  x = t3` | **PASS** |
| **Consecutive Op (Invalid)**| `x = a + * b` | Syntax Error (unexpected operator '*') | **PASS** |
| **Unmatched Paren (Invalid)**| `x = (a + b` | Syntax Error (unbalanced parentheses) | **PASS** |
| **Trailing Op (Invalid)** | `a = b *` | Syntax Error (unexpected end of expression) | **PASS** |
| **Leading Op (Invalid)** | `a = + b` | Syntax Error (unexpected operator '+') | **PASS** |

---

## 🔮 Future Enhancements

1. **Conditional Statements:** TAC generation for `if-else` branching and `goto` labels.
2. **Loop Constructs:** Generating TAC labels and conditional jumps for `while`, `for`, and `do-while` loops.
3. **Function & Procedure Calls:** Support for function parameter pushing, stack frame allocation, and `call`/`return` TAC instructions.
4. **Boolean & Relational Expressions:** Support for relational operators (`<`, `>`, `<=`, `>=`, `==`, `!=`) and short-circuit boolean logic (`&&`, `||`).
5. **TAC Code Optimization:** Intermediate code optimization passes such as Constant Folding, Dead Code Elimination, and Common Subexpression Elimination (CSE).
