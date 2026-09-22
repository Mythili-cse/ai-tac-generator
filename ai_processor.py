"""
AI Processor Module for AI-Driven Three-Address Code Generator.
Integrates official Google Gemini Python SDK (google-genai) to analyze expressions,
precedence, AST evaluation order, and Three-Address Code generation.

Security & Fallback Design:
- Reads GEMINI_API_KEY and GEMINI_MODEL strictly from environment (.env).
- Never exposes keys to frontend.
- When key is missing: returns status 'unavailable' (Gemini API key not configured).
- When Gemini API succeeds: returns status 'active' (Google Gemini AI Active).
- When Gemini API fails: returns status 'error' with actual safe error reason.
"""

import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(override=True)

try:
    from google import genai
    from google.genai import types
    GENAI_SDK_AVAILABLE = True
except ImportError:
    GENAI_SDK_AVAILABLE = False


class AIProcessor:
    """Handles Google Gemini AI API requests for Compiler Design analysis."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

    def is_configured(self) -> bool:
        """Return True if GEMINI_API_KEY is non-empty."""
        return bool(self.api_key)

    def _is_quota_error(self, e: Exception) -> bool:
        """Check if exception is a 429 RESOURCE_EXHAUSTED or quota limit error."""
        err_str = str(e).lower()
        return any(term in err_str for term in ["429", "resource_exhausted", "quota", "rate limit", "rate_limit", "free_tier", "requests"])

    def _generate_with_fallback(self, client: Any, contents: str, system_instruction: str):
        """Try primary GEMINI_MODEL, then fallback models if 404/503/capacity error occurs."""
        candidate_models = [self.model, "gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        unique_models = []
        for m in candidate_models:
            if m and m not in unique_models:
                unique_models.append(m)

        last_exception = None
        for model_name in unique_models:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                return resp, model_name
            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                # Fast fail if quota exhausted to avoid repeated quota retries
                if self._is_quota_error(e):
                    raise e
                if any(k in err_str for k in ["404", "503", "not found", "capacity", "available"]):
                    continue
                raise e
        raise last_exception

    def analyze(self, expression: str, tokens: List[Any], tac_lines: List[str], syntax_analysis: Dict[str, Any], quadruples: Optional[List[Any]] = None, triples: Optional[List[Any]] = None, indirect_triples: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send expression, token info, TAC, Quadruples, Triples, and Indirect Triples to Google Gemini.
        Returns standardized result dict with status: 'active', 'unavailable', 'quota_exceeded', or 'error'.
        """
        if not self.is_configured():
            return {
                "provider": "Google Gemini",
                "status": "unavailable",
                "status_label": "Gemini API key not configured.",
                "result": None,
                "error_message": "GEMINI_API_KEY is missing in environment."
            }

        if not GENAI_SDK_AVAILABLE:
            return {
                "provider": "Google Gemini",
                "status": "error",
                "status_label": "google-genai Python SDK is not installed.",
                "result": None,
                "error_message": "google-genai Python SDK is not installed."
            }

        try:
            client = genai.Client(api_key=self.api_key)

            system_instruction = (
                "You are an expert Compiler Design Assistant specializing in Lexical Analysis, Syntax Parsing, "
                "Operator Precedence, and Intermediate Representations (Three-Address Code, Quadruples, Triples, Indirect Triples). "
                "Analyze the provided arithmetic assignment expression and intermediate representations. "
                "You MUST respond strictly with a valid JSON object matching the requested schema."
            )

            quads_str = json.dumps(quadruples) if quadruples else "N/A"
            trips_str = json.dumps(triples) if triples else "N/A"
            ind_str = json.dumps(indirect_triples) if indirect_triples else "N/A"

            prompt = f"""
Perform a formal Compiler Design analysis for the following arithmetic assignment expression:

Input Expression: {expression}
Tokens: {[t.get('value') for t in tokens]}
Detected Operators: {syntax_analysis.get('operator_count', 0)} operator(s)
Parentheses Status: {syntax_analysis.get('parentheses_status', 'Balanced')}
AST Evaluation Steps: {json.dumps(syntax_analysis.get('evaluation_steps', []))}

Generated Three-Address Code (TAC):
{chr(10).join(tac_lines)}

Generated Quadruples:
{quads_str}

Generated Triples:
{trips_str}

Generated Indirect Triples:
{ind_str}

Required JSON Output Schema:
{{
  "expression_understanding": "Concise compiler-level summary of the expression's mathematical intent.",
  "precedence_explanation": "Detailed explanation of how operator precedence (*, / before +, -) and parentheses grouping were applied.",
  "evaluation_order": ["Step 1...", "Step 2...", "Step 3..."],
  "complexity": "Low" | "Medium" | "High",
  "tac_explanation": "Clear explanation of temporary registers (t1, t2, ...) and intermediate forms (Quadruples/Triples).",
  "optimization_insights": ["Optimization insight 1", "Optimization insight 2"],
  "compiler_notes": "Note on register allocation and intermediate representation efficiency."
}}
"""

            response, used_model = self._generate_with_fallback(client, prompt, system_instruction)

            raw_text = response.text.strip() if response.text else "{}"
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            parsed_json = json.loads(raw_text)

            return {
                "provider": f"Google Gemini ({used_model})",
                "status": "active",
                "status_label": f"Google Gemini AI Active ({used_model})",
                "result": parsed_json,
                "error_message": None
            }

        except Exception as e:
            if self._is_quota_error(e):
                quota_msg = "AI explanation is temporarily unavailable because the Gemini API quota has been reached. TAC generation and intermediate-code generation are still available."
                return {
                    "provider": "Google Gemini",
                    "status": "quota_exceeded",
                    "status_label": "Gemini API Quota Reached",
                    "result": None,
                    "error_message": quota_msg
                }

            err_msg = str(e)
            return {
                "provider": "Google Gemini",
                "status": "error",
                "status_label": f"Gemini API Error: {err_msg}",
                "result": None,
                "error_message": f"Gemini API Error: {err_msg}"
            }

    def explain_with_gemini(self, expression: str, tac_lines: List[str], syntax_analysis: Optional[Dict[str, Any]] = None, quadruples: Optional[List[Any]] = None, triples: Optional[List[Any]] = None, indirect_triples: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query Google Gemini for the 'EXPLAIN WITH AI' button feature.
        """
        if not self.is_configured():
            return {
                "status": "unavailable",
                "status_label": "Gemini API key not configured.",
                "explanation": None,
                "error_message": "GEMINI_API_KEY is not set in .env file."
            }

        if not GENAI_SDK_AVAILABLE:
            return {
                "status": "error",
                "status_label": "google-genai Python SDK is not installed.",
                "explanation": None,
                "error_message": "google-genai Python SDK is not installed."
            }

        try:
            client = genai.Client(api_key=self.api_key)

            system_instruction = (
                "You are an expert Compiler Design Assistant explaining intermediate code generation (TAC, Quadruples, Triples, Indirect Triples) for a university mini project viva demonstration. "
                "Respond ONLY with a valid JSON object."
            )

            eval_steps = syntax_analysis.get('evaluation_steps', []) if syntax_analysis else []
            quads_str = json.dumps(quadruples) if quadruples else "N/A"
            trips_str = json.dumps(triples) if triples else "N/A"
            ind_str = json.dumps(indirect_triples) if indirect_triples else "N/A"

            prompt = f"""
Explain the arithmetic expression and generated intermediate code representations for a compiler design demonstration:

Expression: {expression}
AST Evaluation Order Steps: {json.dumps(eval_steps)}
Generated TAC Instructions:
{chr(10).join(tac_lines)}

Quadruples:
{quads_str}

Triples:
{trips_str}

Indirect Triples:
{ind_str}

Return JSON with exact keys:
{{
  "expression_understanding": "Clear explanation of what the expression calculates and assigns.",
  "precedence_explanation": "Explanation of how parentheses and operator precedence were applied.",
  "evaluation_order": ["1. ...", "2. ...", "3. ..."],
  "complexity": "Low" | "Medium" | "High",
  "tac_explanation": "Detailed explanation of why each temporary variable (t1, t2, ...) was allocated and how Quadruples/Triples represent the operations.",
  "optimization_insights": ["Insight 1...", "Insight 2..."],
  "compiler_notes": "Summary of register reuse and AST post-order traversal."
}}
"""

            resp, used_model = self._generate_with_fallback(client, prompt, system_instruction)

            raw_text = resp.text.strip() if resp.text else "{}"
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw_text)

            return {
                "status": "active",
                "status_label": f"Google Gemini AI Active ({used_model})",
                "model_used": used_model,
                "explanation": parsed,
                "error_message": None
            }

        except Exception as e:
            if self._is_quota_error(e):
                quota_msg = "AI explanation is temporarily unavailable because the Gemini API quota has been reached. TAC generation and intermediate-code generation are still available."
                return {
                    "status": "quota_exceeded",
                    "status_label": "Gemini API Quota Reached",
                    "explanation": None,
                    "error_message": quota_msg
                }

            err_msg = str(e)
            return {
                "status": "error",
                "status_label": f"Gemini API Error: {err_msg}",
                "explanation": None,
                "error_message": f"Gemini API Error: {err_msg}"
            }

