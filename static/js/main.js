/**
 * AI-Driven Three-Address Code Generator
 * Academic Frontend Controller for 3-Screen App Flow (Loading -> Landing -> Compiler Workspace)
 */

let currentTACData = null;
let activeRepTab = 'tac';

document.addEventListener("DOMContentLoaded", () => {
    // Screen 1 Initial Loading Flow
    const screenLoading = document.getElementById("screenLoading");
    const screenLanding = document.getElementById("screenLanding");
    const fill = document.getElementById("loadingProgressFill");
    const termText = document.getElementById("loadingTerminalText");

    const hasLoaded = sessionStorage.getItem("appLoaded");

    if (!hasLoaded) {
        let pct = 0;
        const interval = setInterval(() => {
            pct += 25;
            if (fill) fill.style.width = pct + "%";
            if (pct === 50 && termText) {
                termText.innerText = "Building Abstract Syntax Tree & parser tables...";
            } else if (pct === 75 && termText) {
                termText.innerText = "Deriving Quadruples, Triples & Indirect Triples...";
            }

            if (pct >= 100) {
                clearInterval(interval);
                sessionStorage.setItem("appLoaded", "true");
                setTimeout(() => {
                    if (screenLoading) {
                        screenLoading.style.opacity = "0";
                        setTimeout(() => {
                            screenLoading.classList.add("hidden");
                            if (screenLanding) screenLanding.classList.remove("hidden");
                        }, 400);
                    }
                }, 300);
            }
        }, 300);
    } else {
        if (screenLoading) screenLoading.classList.add("hidden");
        if (screenLanding) screenLanding.classList.remove("hidden");
    }

    // Check Gemini API Health
    checkHealth();
});

/**
 * Transition to Landing Page (Screen 2)
 */
function navigateToLanding() {
    const screenLanding = document.getElementById("screenLanding");
    const screenWorkspace = document.getElementById("screenWorkspace");

    if (screenWorkspace) screenWorkspace.classList.add("hidden");
    if (screenLanding) screenLanding.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Transition to Compiler Workspace (Screen 3)
 */
function navigateToWorkspace() {
    const screenLanding = document.getElementById("screenLanding");
    const screenWorkspace = document.getElementById("screenWorkspace");

    if (screenLanding) screenLanding.classList.add("hidden");
    if (screenWorkspace) screenWorkspace.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Backward compatibility wrapper
 */
function switchPage(page) {
    if (page === 'home' || page === 'landing') {
        navigateToLanding();
    } else {
        navigateToWorkspace();
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
            const explainAiBtn = document.getElementById("explainAiBtn");

            if (data.gemini_configured) {
                if (aiStatusText) aiStatusText.innerText = "Google Gemini AI model active. Click 'EXPLAIN WITH AI' for dynamic breakdown.";
                if (aiBrandTag) aiBrandTag.classList.remove("hidden");
                if (explainAiBtn) explainAiBtn.disabled = false;
            } else {
                if (aiStatusText) aiStatusText.innerText = "AI explanation temporarily unavailable. Compiler generation remains fully functional.";
                if (aiBrandTag) aiBrandTag.classList.add("hidden");
                if (explainAiBtn) explainAiBtn.disabled = true;
            }
        }
    } catch (e) {
        console.warn("Health check failed.", e);
    }
}

/**
 * Load preset example into textarea
 */
function loadExample(expr) {
    const textarea = document.getElementById("expressionInput");
    if (textarea) textarea.value = expr;
}

/**
 * Reset workspace inputs, status badges, and results
 */
function resetStudio() {
    const textarea = document.getElementById("expressionInput");
    if (textarea) textarea.value = "";
    
    const errBanner = document.getElementById("errorBanner");
    if (errBanner) errBanner.classList.add("hidden");
    
    const resSec = document.getElementById("resultsSection");
    if (resSec) resSec.classList.add("hidden");
    
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
 * Send expression to Flask API /api/generate
 */
async function generateTAC() {
    const inputEl = document.getElementById("expressionInput");
    const input = inputEl ? inputEl.value.trim() : "";
    const errorBanner = document.getElementById("errorBanner");
    const loadingSpinner = document.getElementById("loadingSpinner");
    const resultsSection = document.getElementById("resultsSection");

    if (errorBanner) errorBanner.classList.add("hidden");
    if (resultsSection) resultsSection.classList.add("hidden");
    resetOverviewStages();

    if (!input) {
        showError("Validation Error", "Please enter an arithmetic assignment expression.");
        return;
    }

    if (loadingSpinner) loadingSpinner.classList.remove("hidden");

    try {
        const response = await fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ expression: input })
        });

        const data = await response.json();
        if (loadingSpinner) loadingSpinner.classList.add("hidden");

        if (!response.ok || !data.success) {
            showError(data.stage || "Compiler Diagnostic Error", data.error || "Failed to generate TAC.");
            return;
        }

        currentTACData = data;
        completeOverviewStages();
        renderResults(data);

    } catch (err) {
        if (loadingSpinner) loadingSpinner.classList.add("hidden");
        showError("Server Connection Error", "Could not connect to Flask backend server. Ensure app.py is running.");
        console.error(err);
    }
}

/**
 * Render all API response data into the Workspace sections
 */
function renderResults(data) {
    // 1. Dynamic Metadata
    const instrBadge = document.getElementById("instrCountBadge");
    const tempBadge = document.getElementById("tempCountBadge");
    const execBadge = document.getElementById("execTimeBadge");

    if (instrBadge) instrBadge.innerText = `${data.tac_meta.instruction_count} instructions`;
    if (tempBadge) tempBadge.innerText = `${data.tac_meta.temporary_count} temporaries`;
    if (execBadge) execBadge.innerText = `${data.tac_meta.execution_time_ms} ms`;

    // 2. TAB 1: Three-Address Code Panel
    const tacContainer = document.getElementById("tacCodeContainer");
    if (tacContainer) {
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
    }

    // 3. TAB 2: Quadruples Table
    const quadruplesBody = document.getElementById("quadruplesTableBody");
    if (quadruplesBody) {
        quadruplesBody.innerHTML = "";
        if (data.quadruples && data.quadruples.length > 0) {
            data.quadruples.forEach(q => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td><code>(${q.index})</code></td>
                    <td><code class="op-badge">${escapeHtml(q.op)}</code></td>
                    <td><code>${escapeHtml(q.arg1)}</code></td>
                    <td><code>${escapeHtml(q.arg2)}</code></td>
                    <td><code class="res-badge">${escapeHtml(q.result)}</code></td>
                `;
                quadruplesBody.appendChild(row);
            });
        } else {
            quadruplesBody.innerHTML = '<tr><td colspan="5">No Quadruples generated.</td></tr>';
        }
    }

    // 4. TAB 3: Triples Table
    const triplesBody = document.getElementById("triplesTableBody");
    if (triplesBody) {
        triplesBody.innerHTML = "";
        if (data.triples && data.triples.length > 0) {
            data.triples.forEach(t => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td><code>${escapeHtml(t.index)}</code></td>
                    <td><code class="op-badge">${escapeHtml(t.op)}</code></td>
                    <td><code>${escapeHtml(t.arg1)}</code></td>
                    <td><code>${escapeHtml(t.arg2)}</code></td>
                `;
                triplesBody.appendChild(row);
            });
        } else {
            triplesBody.innerHTML = '<tr><td colspan="4">No Triples generated.</td></tr>';
        }
    }

    // 5. TAB 4: Indirect Triples Tables
    const indPointersBody = document.getElementById("indirectPointersBody");
    if (indPointersBody) {
        indPointersBody.innerHTML = "";
        if (data.indirect_triples && data.indirect_triples.pointers) {
            data.indirect_triples.pointers.forEach(p => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td><code class="ptr-badge">${escapeHtml(p.pointer)}</code></td>
                    <td><code class="ref-badge">${escapeHtml(p.triple_ref)}</code></td>
                `;
                indPointersBody.appendChild(row);
            });
        }
    }

    const indTriplesBody = document.getElementById("indirectTriplesBody");
    if (indTriplesBody) {
        indTriplesBody.innerHTML = "";
        if (data.indirect_triples && data.indirect_triples.triples) {
            data.indirect_triples.triples.forEach(t => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td><code>${escapeHtml(t.index)}</code></td>
                    <td><code class="op-badge">${escapeHtml(t.op)}</code></td>
                    <td><code>${escapeHtml(t.arg1)}</code></td>
                    <td><code>${escapeHtml(t.arg2)}</code></td>
                `;
                indTriplesBody.appendChild(row);
            });
        }
    }

    // 6. Compiler Analysis Grid
    const syn = data.syntax_analysis;
    const synStatus = document.getElementById("synStatus");
    if (synStatus) {
        synStatus.innerText = syn.syntax_status;
        synStatus.className = syn.syntax_status === "VALID" ? "an-val val-good" : "an-val";
    }

    const synParen = document.getElementById("synParen");
    const synOps = document.getElementById("synOps");
    const synOperands = document.getElementById("synOperands");
    const synAssign = document.getElementById("synAssign");
    const synPrecedence = document.getElementById("synPrecedence");

    if (synParen) synParen.innerText = syn.parentheses_status.toUpperCase();
    if (synOps) synOps.innerText = syn.operator_count;
    if (synOperands) synOperands.innerText = syn.operand_count;
    if (synAssign) synAssign.innerText = syn.assignment_status.toUpperCase();
    if (synPrecedence) synPrecedence.innerText = syn.precedence_status.toUpperCase();

    // Evaluation Order List
    const evalList = document.getElementById("evalOrderList");
    if (evalList) {
        evalList.innerHTML = "";
        if (syn.evaluation_steps) {
            syn.evaluation_steps.forEach(step => {
                const li = document.createElement("li");
                li.innerText = step;
                evalList.appendChild(li);
            });
        }
    }

    // 7. Lexical Analysis Tokens Table
    const tokensTableBody = document.getElementById("tokensTableBody");
    if (tokensTableBody) {
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
    }

    // 8. TAC Validation Checklist
    const val = data.validation;
    const checklist = document.getElementById("validationChecklist");
    if (checklist) {
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
    }

    const valSummary = document.getElementById("validationSummary");
    if (valSummary) valSummary.innerText = val.summary;

    // 9. AI Explanation Section State
    const ai = data.ai || {};
    const aiStatusText = document.getElementById("aiStatusText");
    const aiBrandTag = document.getElementById("aiBrandTag");
    const explainAiBtn = document.getElementById("explainAiBtn");

    if (ai.status === "active") {
        if (aiStatusText) aiStatusText.innerText = "Google Gemini AI model active. Click 'EXPLAIN WITH AI' for dynamic breakdown.";
        if (aiBrandTag) aiBrandTag.classList.remove("hidden");
        if (explainAiBtn) {
            explainAiBtn.disabled = false;
            explainAiBtn.classList.remove("btn-disabled");
            explainAiBtn.title = "Click to generate AI explanation";
        }
    } else {
        if (aiStatusText) aiStatusText.innerText = "AI explanation temporarily unavailable. Compiler generation remains fully functional.";
        if (aiBrandTag) aiBrandTag.classList.add("hidden");
        if (explainAiBtn) {
            explainAiBtn.disabled = true;
            explainAiBtn.classList.add("btn-disabled");
            explainAiBtn.title = "AI explanation temporarily unavailable.";
        }
    }

    // Reset representation tab to TAC by default
    switchRepTab('tac');

    // Reveal Results Section
    const resultsSec = document.getElementById("resultsSection");
    if (resultsSec) resultsSec.classList.remove("hidden");
}

/**
 * Display diagnostic error box
 */
function showError(stage, msg) {
    const banner = document.getElementById("errorBanner");
    const stageEl = document.getElementById("errorStage");
    const msgEl = document.getElementById("errorMessage");

    if (stageEl) stageEl.innerText = stage;
    if (msgEl) msgEl.innerText = msg;
    if (banner) banner.classList.remove("hidden");
}

/**
 * Switch intermediate representation tab (tac, quadruples, triples, indirect)
 */
function switchRepTab(tab) {
    activeRepTab = tab;

    const tabs = [
        { key: 'tac', btn: 'tabBtnTac', view: 'repViewTac', label: 'TAC' },
        { key: 'quadruples', btn: 'tabBtnQuad', view: 'repViewQuadruples', label: 'Quadruples' },
        { key: 'triples', btn: 'tabBtnTrip', view: 'repViewTriples', label: 'Triples' },
        { key: 'indirect', btn: 'tabBtnInd', view: 'repViewIndirect', label: 'Indirect Triples' }
    ];

    tabs.forEach(item => {
        const btnEl = document.getElementById(item.btn);
        const viewEl = document.getElementById(item.view);
        if (btnEl && viewEl) {
            if (item.key === tab) {
                btnEl.classList.add("active");
                viewEl.classList.remove("hidden");
            } else {
                btnEl.classList.remove("active");
                viewEl.classList.add("hidden");
            }
        }
    });

    const activeObj = tabs.find(t => t.key === tab) || tabs[0];
    const copyBtn = document.getElementById("copyRepBtn");
    const dlBtn = document.getElementById("downloadRepBtn");
    if (copyBtn) copyBtn.innerHTML = `<i class="fa-regular fa-copy"></i> COPY ${activeObj.label.toUpperCase()}`;
    if (dlBtn) dlBtn.innerHTML = `<i class="fa-solid fa-download"></i> DOWNLOAD ${activeObj.label.toUpperCase()}`;
}

/**
 * Dynamic Copy handler
 */
function copyCurrentRep() {
    if (!currentTACData) return;

    let content = "";
    let label = "Representation";

    if (activeRepTab === 'tac' && currentTACData.tac_details) {
        label = "Three-Address Code";
        content = currentTACData.tac_details.map(i => i.full_line).join("\n");
    } else if (activeRepTab === 'quadruples' && currentTACData.quadruples) {
        label = "Quadruples";
        content = "Index\tOp\tArg1\tArg2\tResult\n" +
            currentTACData.quadruples.map(q => `(${q.index})\t${q.op}\t${q.arg1}\t${q.arg2}\t${q.result}`).join("\n");
    } else if (activeRepTab === 'triples' && currentTACData.triples) {
        label = "Triples";
        content = "Index\tOp\tArg1\tArg2\n" +
            currentTACData.triples.map(t => `${t.index}\t${t.op}\t${t.arg1}\t${t.arg2}`).join("\n");
    } else if (activeRepTab === 'indirect' && currentTACData.indirect_triples) {
        label = "Indirect Triples";
        const ptrs = currentTACData.indirect_triples.pointers || [];
        const trips = currentTACData.indirect_triples.triples || [];
        content = "INDIRECT TRIPLE POINTER TABLE\nPointer\tTriple Reference\n" +
            ptrs.map(p => `${p.pointer}\t${p.triple_ref}`).join("\n") +
            "\n\nTRIPLES TABLE\nIndex\tOp\tArg1\tArg2\n" +
            trips.map(t => `${t.index}\t${t.op}\t${t.arg1}\t${t.arg2}`).join("\n") +
            "\n\nIndirect triples use a separate pointer table to reference triple statements.";
    }

    if (!content) return;
    navigator.clipboard.writeText(content);
    alert(`${label} copied to clipboard!`);
}

/**
 * Dynamic Download handler
 */
function downloadCurrentRep() {
    if (!currentTACData) return;

    let content = "";
    let ext = "txt";
    let label = "representation";

    const header = `; AI-Driven Three-Address Code Generator\n; Target Variable: ${currentTACData.target_variable}\n; Input Expression: ${currentTACData.expression}\n\n`;

    if (activeRepTab === 'tac' && currentTACData.tac_details) {
        label = "tac";
        ext = "tac";
        content = header + currentTACData.tac_details.map(i => i.full_line).join("\n");
    } else if (activeRepTab === 'quadruples' && currentTACData.quadruples) {
        label = "quadruples";
        ext = "quad";
        content = header + "Index\tOp\tArg1\tArg2\tResult\n" +
            currentTACData.quadruples.map(q => `(${q.index})\t${q.op}\t${q.arg1}\t${q.arg2}\t${q.result}`).join("\n");
    } else if (activeRepTab === 'triples' && currentTACData.triples) {
        label = "triples";
        ext = "trip";
        content = header + "Index\tOp\tArg1\tArg2\n" +
            currentTACData.triples.map(t => `${t.index}\t${t.op}\t${t.arg1}\t${t.arg2}`).join("\n");
    } else if (activeRepTab === 'indirect' && currentTACData.indirect_triples) {
        label = "indirect_triples";
        ext = "ind";
        const ptrs = currentTACData.indirect_triples.pointers || [];
        const trips = currentTACData.indirect_triples.triples || [];
        content = header + "INDIRECT TRIPLE POINTER TABLE\nPointer\tTriple Reference\n" +
            ptrs.map(p => `${p.pointer}\t${p.triple_ref}`).join("\n") +
            "\n\nTRIPLES TABLE\nIndex\tOp\tArg1\tArg2\n" +
            trips.map(t => `${t.index}\t${t.op}\t${t.arg1}\t${t.arg2}`).join("\n") +
            "\n\nIndirect triples use a separate pointer table to reference triple statements.\n";
    }

    if (!content) return;
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `expression_${currentTACData.target_variable}_${label}.${ext}`;
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
    
    if (modal) modal.classList.remove("hidden");
    if (modalContent) {
        modalContent.innerHTML = `
            <div class="spinner"></div>
            <p style="text-align:center;">Querying Google Gemini AI Explanation Service...</p>
        `;
    }

    try {
        const resp = await fetch("/api/explain", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                expression: currentTACData.expression,
                tac: currentTACData.tac,
                syntax_analysis: currentTACData.syntax_analysis,
                quadruples: currentTACData.quadruples,
                triples: currentTACData.triples,
                indirect_triples: currentTACData.indirect_triples
            })
        });

        const data = await resp.json();
        if (resp.ok && data.success) {
            const aiData = data.ai_explanation;
            
            if (aiData.status === "quota_exceeded" || (aiData.error_message && (aiData.error_message.toLowerCase().includes("quota") || aiData.error_message.includes("429") || aiData.error_message.toLowerCase().includes("resource_exhausted")))) {
                modalContent.innerHTML = `
                    <div style="color:var(--status-warning); font-weight:600; margin-bottom:8px;">
                        Gemini API Quota Reached
                    </div>
                    <p style="color:var(--text-muted); font-size:0.85rem;">
                        AI explanation temporarily unavailable. Compiler generation remains fully functional.
                    </p>
                `;
                return;
            }

            if (aiData.status === "unavailable") {
                modalContent.innerHTML = `
                    <div style="color:var(--status-error); font-weight:600; margin-bottom:8px;">
                        Gemini API key not configured.
                    </div>
                    <p style="color:var(--text-muted); font-size:0.85rem;">
                        To enable live Google Gemini AI explanations, configure <code>GEMINI_API_KEY</code> in the <code>.env</code> file.
                        Compiler generation remains fully functional.
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
                <p style="color:var(--text-body); margin-bottom:10px;">${escapeHtml(exp.expression_understanding || '')}</p>

                <h4 style="color:var(--text-main); margin-top:10px;">Precedence Explanation</h4>
                <p style="color:var(--text-body); margin-bottom:10px;">${escapeHtml(exp.precedence_explanation || '')}</p>

                <h4 style="color:var(--text-main); margin-top:10px;">Evaluation Order</h4>
                <ol style="padding-left:20px; color:var(--text-body); margin-bottom:10px;">
                    ${evalItems.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                </ol>

                <h4 style="color:var(--text-main); margin-top:10px;">Complexity</h4>
                <p style="color:var(--accent-primary); font-weight:600; margin-bottom:10px;">${escapeHtml(exp.complexity || 'Medium')}</p>

                <h4 style="color:var(--text-main); margin-top:10px;">TAC Explanation</h4>
                <p style="color:var(--text-body); margin-bottom:10px;">${escapeHtml(exp.tac_explanation || '')}</p>

                <h4 style="color:var(--text-main); margin-top:10px;">Optimization Insights</h4>
                <ul style="padding-left:20px; color:var(--text-body); margin-bottom:10px;">
                    ${insights.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                </ul>

                ${exp.compiler_notes ? `
                    <h4 style="color:var(--text-main); margin-top:10px;">Compiler Notes</h4>
                    <p style="color:var(--text-body); margin-bottom:10px;">${escapeHtml(exp.compiler_notes)}</p>
                ` : ''}
            `;
        } else {
            modalContent.innerHTML = `<p style="color:var(--status-error);">Could not generate explanation.</p>`;
        }
    } catch (err) {
        if (modalContent) modalContent.innerHTML = `<p style="color:var(--status-error);">Error connecting to explanation service: ${escapeHtml(String(err))}</p>`;
    }
}

/**
 * Close AI modal dialog
 */
function closeAIModal() {
    const modal = document.getElementById("aiModal");
    if (modal) modal.classList.add("hidden");
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
