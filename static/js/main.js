/**
 * AI-Driven Three-Address Code Generator
 * Academic Frontend Controller for Page Navigation, Compiler Workbench Pipeline, and API Integration
 */

let currentTACData = null;

document.addEventListener("DOMContentLoaded", () => {
    // Check API health to update initial AI status
    checkHealth();

    // Default view is Page 1 (Home Page)
    switchPage('home');
});

/**
 * Switch between Page 1 (Home) and Page 2 (Generator Workbench)
 * @param {'home' | 'generator'} page 
 */
function switchPage(page) {
    const pageHome = document.getElementById("pageHome");
    const pageGenerator = document.getElementById("pageGenerator");

    if (page === 'generator') {
        pageHome.classList.add("hidden");
        pageGenerator.classList.remove("hidden");
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        pageGenerator.classList.add("hidden");
        pageHome.classList.remove("hidden");
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Query health endpoint to check Gemini configuration
 */
async function checkHealth() {
    try {
        const resp = await fetch("/api/health");
        if (resp.ok) {
            const data = await resp.json();
            const aiStatusText = document.getElementById("aiStatusText");
            const aiBrandTag = document.getElementById("aiBrandTag");

            if (data.gemini_configured) {
                aiStatusText.innerText = "Google Gemini AI configured. Click 'EXPLAIN WITH AI' for dynamic intermediate code explanation.";
                aiBrandTag.classList.remove("hidden");
            } else {
                aiStatusText.innerText = "Gemini API key not configured.";
                aiBrandTag.classList.add("hidden");
            }
        }
    } catch (e) {
        console.warn("Health check failed.", e);
    }
}

/**
 * Load preset example into textarea and auto-trigger TAC generation
 * @param {string} expr 
 */
function loadExample(expr) {
    const textarea = document.getElementById("expressionInput");
    textarea.value = expr;
    generateTAC();
}

/**
 * Reset studio inputs, overview stage badges, and results
 */
function resetStudio() {
    document.getElementById("expressionInput").value = "";
    document.getElementById("errorBanner").classList.add("hidden");
    document.getElementById("resultsSection").classList.add("hidden");
    resetOverviewStages();
}

/**
 * Reset Compiler Overview stage status badges to READY
 */
function resetOverviewStages() {
    const stages = ["stgInput", "stgLexer", "stgParser", "stgTac", "stgVal"];
    stages.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.className = "stg-status status-ready";
            el.innerText = "READY";
        }
    });
}

/**
 * Mark Compiler Overview stage status badges as COMPLETED
 */
function completeOverviewStages() {
    const stages = ["stgInput", "stgLexer", "stgParser", "stgTac", "stgVal"];
    stages.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.className = "stg-status status-completed";
            el.innerText = "✓ COMPLETED";
        }
    });
}

/**
 * Primary function sending expression to Flask API /api/generate
 */
async function generateTAC() {
    const input = document.getElementById("expressionInput").value.trim();
    const errorBanner = document.getElementById("errorBanner");
    const loadingSpinner = document.getElementById("loadingSpinner");
    const resultsSection = document.getElementById("resultsSection");

    errorBanner.classList.add("hidden");
    resultsSection.classList.add("hidden");
    resetOverviewStages();

    if (!input) {
        showError("Validation Error", "Please enter an arithmetic assignment expression.");
        return;
    }

    loadingSpinner.classList.remove("hidden");

    try {
        const response = await fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ expression: input })
        });

        const data = await response.json();
        loadingSpinner.classList.add("hidden");

        if (!response.ok || !data.success) {
            showError(data.stage || "Compiler Diagnostic Error", data.error || "Failed to generate TAC.");
            return;
        }

        currentTACData = data;
        completeOverviewStages();
        renderResults(data);

    } catch (err) {
        loadingSpinner.classList.add("hidden");
        showError("Server Connection Error", "Could not connect to Flask backend server. Ensure app.py is running.");
        console.error(err);
    }
}

/**
 * Render all API response data into the Workbench page sections
 */
function renderResults(data) {
    // 1. Dynamic Metadata
    document.getElementById("instrCountBadge").innerText = `${data.tac_meta.instruction_count} instructions`;
    document.getElementById("tempCountBadge").innerText = `${data.tac_meta.temporary_count} temporaries`;
    document.getElementById("execTimeBadge").innerText = `${data.tac_meta.execution_time_ms} ms`;

    // 2. TAC Code Editor Block
    const tacContainer = document.getElementById("tacCodeContainer");
    tacContainer.innerHTML = "";

    if (data.tac_details && data.tac_details.length > 0) {
        data.tac_details.forEach(item => {
            const lineDiv = document.createElement("div");
            lineDiv.className = "tac-line";
            lineDiv.innerHTML = `
                <span class="tac-line-num">${item.line_no}</span>
                <span class="tac-text">${escapeHtml(item.text)}</span>
            `;
            tacContainer.appendChild(lineDiv);
        });
    } else {
        tacContainer.innerHTML = '<div class="tac-line"><span class="tac-text">No TAC instructions generated.</span></div>';
    }

    // 3. Compiler Analysis Grid
    const syn = data.syntax_analysis;
    const synStatus = document.getElementById("synStatus");
    synStatus.innerText = syn.syntax_status;
    synStatus.className = syn.syntax_status === "VALID" ? "an-val val-good" : "an-val";

    document.getElementById("synParen").innerText = syn.parentheses_status.toUpperCase();
    document.getElementById("synOps").innerText = syn.operator_count;
    document.getElementById("synOperands").innerText = syn.operand_count;
    document.getElementById("synAssign").innerText = syn.assignment_status.toUpperCase();
    document.getElementById("synPrecedence").innerText = syn.precedence_status.toUpperCase();

    // Evaluation Order List
    const evalList = document.getElementById("evalOrderList");
    evalList.innerHTML = "";
    if (syn.evaluation_steps) {
        syn.evaluation_steps.forEach(step => {
            const li = document.createElement("li");
            li.innerText = step;
            evalList.appendChild(li);
        });
    }

    // 4. Lexical Analysis Tokens Table (4 columns)
    const tokensTableBody = document.getElementById("tokensTableBody");
    tokensTableBody.innerHTML = "";

    data.tokens.forEach(tok => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td><code>${tok.position}</code></td>
            <td><code>${tok.type}</code></td>
            <td><code>${escapeHtml(tok.value)}</code></td>
            <td>${tok.category || 'Token'}</td>
        `;
        tokensTableBody.appendChild(row);
    });

    // 5. TAC Validation Report Checklist
    const val = data.validation;
    const checklist = document.getElementById("validationChecklist");
    checklist.innerHTML = "";

    val.checks.forEach(check => {
        const isPass = check.status === "PASSED";
        const item = document.createElement("div");
        item.className = "check-item";
        item.innerHTML = `
            <span class="check-icon-mark">${isPass ? '✓' : '✗'}</span>
            <span class="check-title-text">${check.name}: ${check.detail}</span>
        `;
        checklist.appendChild(item);
    });

    document.getElementById("validationSummary").innerText = val.summary;

    // 6. Optional AI Explanation Section State
    const ai = data.ai || {};
    const aiStatusText = document.getElementById("aiStatusText");
    const aiBrandTag = document.getElementById("aiBrandTag");

    if (ai.status === "active") {
        aiStatusText.innerText = "Google Gemini AI analysis active. Click 'EXPLAIN WITH AI' for full breakdown.";
        aiBrandTag.classList.remove("hidden");
    } else if (ai.status === "error") {
        aiStatusText.innerText = `Gemini API Error: ${ai.error_message || 'API call failed.'}`;
        aiBrandTag.classList.add("hidden");
    } else {
        aiStatusText.innerText = "Gemini API key not configured.";
        aiBrandTag.classList.add("hidden");
    }

    // Reveal Results Section
    document.getElementById("resultsSection").classList.remove("hidden");
}

/**
 * Display diagnostic error box
 */
function showError(stage, msg) {
    const banner = document.getElementById("errorBanner");
    document.getElementById("errorStage").innerText = stage;
    document.getElementById("errorMessage").innerText = msg;
    banner.classList.remove("hidden");
}

/**
 * Copy TAC code to clipboard
 */
function copyTAC() {
    if (!currentTACData || !currentTACData.tac_details) return;
    const codeText = currentTACData.tac_details.map(i => i.full_line).join("\n");

    navigator.clipboard.writeText(codeText);
    alert("Three-Address Code copied to clipboard!");
}

/**
 * Download TAC file (.tac format)
 */
function downloadTAC() {
    if (!currentTACData || !currentTACData.tac_details) return;
    
    const header = `; AI-Driven Three-Address Code Generator\n; Target Variable: ${currentTACData.target_variable}\n; Input Expression: ${currentTACData.expression}\n\n`;
    const body = currentTACData.tac_details.map(i => i.full_line).join("\n");
    const content = header + body;

    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `expression_${currentTACData.target_variable}.tac`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Explain with AI modal dialog handler
 */
async function explainWithAI() {
    if (!currentTACData) return;
    const modal = document.getElementById("aiModal");
    const modalContent = document.getElementById("modalContent");
    
    modal.classList.remove("hidden");
    modalContent.innerHTML = `
        <div class="spinner"></div>
        <p style="text-align:center;">Querying Google Gemini AI Explanation Service...</p>
    `;

    try {
        const resp = await fetch("/api/explain", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                expression: currentTACData.expression,
                tac: currentTACData.tac,
                syntax_analysis: currentTACData.syntax_analysis
            })
        });

        const data = await resp.json();
        if (resp.ok && data.success) {
            const aiData = data.ai_explanation;
            
            if (aiData.status === "unavailable") {
                modalContent.innerHTML = `
                    <div style="color:var(--status-error); font-weight:600; margin-bottom:8px;">
                        Gemini API key not configured.
                    </div>
                    <p style="color:var(--text-muted); font-size:0.85rem;">
                        To enable live Google Gemini AI explanations, configure <code>GEMINI_API_KEY</code> in the <code>.env</code> file.
                        Compiler TAC generation remains 100% functional.
                    </p>
                `;
                return;
            }

            if (aiData.status === "error") {
                modalContent.innerHTML = `
                    <div style="color:var(--status-error); font-weight:600; margin-bottom:8px;">
                        Gemini API Error
                    </div>
                    <p style="color:var(--text-muted); font-size:0.85rem;">
                        ${escapeHtml(aiData.error_message || 'Gemini API call failed.')}
                    </p>
                `;
                return;
            }

            const exp = aiData.explanation || {};
            const evalItems = exp.evaluation_order || [];
            const insights = exp.optimization_insights || [];

            modalContent.innerHTML = `
                <div style="margin-bottom:14px; color:var(--accent-secondary); font-weight:600; font-size:0.85rem;">
                    Powered by Google Gemini
                </div>
                
                <h4 style="color:var(--accent-primary); margin-top:10px;">Expression Understanding</h4>
                <p style="color:var(--text-muted); margin-bottom:10px;">${escapeHtml(exp.expression_understanding || '')}</p>

                <h4 style="color:var(--text-primary); margin-top:10px;">Precedence Explanation</h4>
                <p style="color:var(--text-muted); margin-bottom:10px;">${escapeHtml(exp.precedence_explanation || '')}</p>

                <h4 style="color:var(--text-primary); margin-top:10px;">Evaluation Order</h4>
                <ol style="padding-left:20px; color:var(--text-muted); margin-bottom:10px;">
                    ${evalItems.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                </ol>

                <h4 style="color:var(--text-primary); margin-top:10px;">Complexity</h4>
                <p style="color:var(--accent-primary); font-weight:600; margin-bottom:10px;">${escapeHtml(exp.complexity || 'Medium')}</p>

                <h4 style="color:var(--text-primary); margin-top:10px;">TAC Explanation</h4>
                <p style="color:var(--text-muted); margin-bottom:10px;">${escapeHtml(exp.tac_explanation || '')}</p>

                <h4 style="color:var(--text-primary); margin-top:10px;">Optimization Insights</h4>
                <ul style="padding-left:20px; color:var(--text-muted); margin-bottom:10px;">
                    ${insights.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                </ul>

                ${exp.compiler_notes ? `
                    <h4 style="color:var(--text-primary); margin-top:10px;">Compiler Notes</h4>
                    <p style="color:var(--text-muted); margin-bottom:10px;">${escapeHtml(exp.compiler_notes)}</p>
                ` : ''}
            `;
        } else {
            modalContent.innerHTML = `<p style="color:var(--status-error);">Could not generate explanation.</p>`;
        }
    } catch (err) {
        modalContent.innerHTML = `<p style="color:var(--status-error);">Error connecting to explanation service: ${escapeHtml(String(err))}</p>`;
    }
}

/**
 * Close AI modal dialog
 */
function closeAIModal() {
    document.getElementById("aiModal").classList.add("hidden");
}

/**
 * Helper to escape HTML characters
 */
function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, "&amp;")
                      .replace(/</g, "&lt;")
                      .replace(/>/g, "&gt;")
                      .replace(/"/g, "&quot;")
                      .replace(/'/g, "&#039;");
}
