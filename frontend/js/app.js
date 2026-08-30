document.addEventListener("DOMContentLoaded", () => {
    initTabNavigation();
    checkSystemHealth();
    loadDocumentList();
    initChatForm();
    initDocumentUploader();
    initCameraControls();

    // Periodic telemetry loop (every 3s)
    setInterval(() => {
        updateNavigationTelemetry();
    }, 3000);
});

/* Tab Switcher */
function initTabNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const tabContents = document.querySelectorAll(".tab-content");
    const pageTitle = document.getElementById("page-title");

    const titleMap = {
        "dashboard": "Autonomous Navigation Dashboard",
        "vision": "Vision & Perception System",
        "chatbot": "AI Assistant & RAG Knowledge Engine",
        "documents": "Document Analyzer & Vector Store",
        "navigation": "Autonomous Navigation Logic Controller"
    };

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");

            navItems.forEach(n => n.classList.remove("active"));
            tabContents.forEach(t => t.classList.remove("active"));

            item.classList.add("active");
            document.getElementById(`tab-${targetTab}`).classList.add("active");
            pageTitle.textContent = titleMap[targetTab] || "Autonomous Navigation Dashboard";
        });
    });
}

/* System Health Check */
async function checkSystemHealth() {
    try {
        const res = await fetch("/health");
        if (res.ok) {
            const data = await res.json();
            
            // Update Mini Status
            const miniGemini = document.getElementById("mini-gemini-status");
            if (miniGemini) {
                if (data.gemini_api_key_configured) {
                    miniGemini.textContent = "Connected";
                    miniGemini.className = "status-tag green";
                } else {
                    miniGemini.textContent = "Simulation Mode";
                    miniGemini.className = "status-tag";
                }
            }

            // Update Top Health Badges
            const components = data.components || {};
            
            // Gemini API
            if (data.gemini_api_key_configured) {
                updateStatusBadge("badge-gemini", "Gemini API", "CONNECTED", "success");
            } else {
                updateStatusBadge("badge-gemini", "Gemini API", "NOT CONFIGURED", "warning");
            }
            
            // Embeddings
            const embStatus = components.embeddings === "ready" ? "READY" : "ERROR";
            updateStatusBadge("badge-embeddings", "Embeddings", embStatus, embStatus === "READY" ? "success" : "error");
            
            // ChromaDB
            const dbStatus = components.vector_database === "ready" ? "READY" : "ERROR";
            updateStatusBadge("badge-vectordb", "ChromaDB", dbStatus, dbStatus === "READY" ? "success" : "error");
            
            // RAG
            const ragStatus = components.rag_engine === "active" ? "READY" : "ERROR";
            updateStatusBadge("badge-rag", "RAG", ragStatus, ragStatus === "READY" ? "success" : "error");
            
            // Vision
            const visionStatus = components.vision_system === "ready" ? "READY" : "ERROR";
            updateStatusBadge("badge-vision", "Vision", visionStatus, visionStatus === "READY" ? "success" : "error");
            
            // MCP Tools
            const mcpStatus = components.mcp_tools === "ready" ? "READY" : "ERROR";
            updateStatusBadge("badge-mcp", "MCP Tools", mcpStatus, mcpStatus === "READY" ? "success" : "error");

            // Vector DB stats
            const stats = data.vector_db_stats || {};
            const totalChunks = document.getElementById("stat-total-chunks");
            if (totalChunks) totalChunks.textContent = stats.total_chunks || 0;
        }
    } catch (err) {
        console.error("Health check error:", err);
    }
}

function updateStatusBadge(badgeId, label, statusText, statusType) {
    const badge = document.getElementById(badgeId);
    if (!badge) return;
    
    let dotColor = "green";
    if (statusType === "warning") dotColor = "yellow";
    if (statusType === "error") dotColor = "red";
    
    badge.innerHTML = `<span class="dot ${dotColor}"></span> ${label}: ${statusText}`;
}

/* Document Analyzer & Vector List */
async function loadDocumentList() {
    try {
        const res = await fetch("/documents");
        if (res.ok) {
            const data = await res.json();
            const docs = data.documents || [];
            const statDocs = document.getElementById("stat-total-docs");
            if (statDocs) statDocs.textContent = docs.length;

            const container = document.getElementById("doc-list-container");
            if (!container) return;
            container.innerHTML = "";

            if (docs.length === 0) {
                container.innerHTML = "<li class='doc-item'><p class='text-muted'>No custom documents uploaded yet.</p></li>";
                return;
            }

            docs.forEach(doc => {
                const li = document.createElement("li");
                li.className = "doc-item";
                li.innerHTML = `
                    <div class="doc-info">
                        <h4><i class="fa-solid fa-file-lines"></i> ${doc.filename}</h4>
                        <p>${doc.chunk_count} Chunks | ${doc.file_size_kb} KB | Status: ${doc.status}</p>
                    </div>
                    <button class="btn btn-sm btn-danger" onclick="deleteDocument('${doc.id}')">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                `;
                container.appendChild(li);
            });
        }
    } catch (err) {
        console.error("Error loading document list:", err);
    }
}

function initDocumentUploader() {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("doc-file-input");
    const statusBox = document.getElementById("doc-upload-status");
    if (!dropZone || !fileInput || !statusBox) return;

    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "var(--primary)";
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.style.borderColor = "var(--border-color)";
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "var(--border-color)";
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) {
            handleFileUpload(fileInput.files[0]);
        }
    });

    async function handleFileUpload(file) {
        statusBox.textContent = `Uploading and processing '${file.name}'...`;
        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/documents/upload", {
                method: "POST",
                body: formData
            });

            if (res.ok) {
                const result = await res.json();
                statusBox.textContent = `Successfully indexed '${file.name}' into ${result.document.chunk_count} vector chunks!`;
                statusBox.style.color = "var(--success)";
                loadDocumentList();
                checkSystemHealth();
            } else {
                const errData = await res.json();
                statusBox.textContent = `Upload error: ${errData.detail}`;
                statusBox.style.color = "var(--danger)";
            }
        } catch (err) {
            statusBox.textContent = `Upload failed: ${err.message}`;
            statusBox.style.color = "var(--danger)";
        }
    }
}

async function deleteDocument(docId) {
    if (!confirm("Are you sure you want to delete this document from the vector store?")) return;
    try {
        const res = await fetch(`/documents/${docId}`, { method: "DELETE" });
        if (res.ok) {
            loadDocumentList();
            checkSystemHealth();
        }
    } catch (err) {
        console.error("Delete document error:", err);
    }
}

async function clearVectorDatabase() {
    if (!confirm("Are you sure you want to clear the entire vector store?")) return;
    try {
        const res = await fetch("/documents/clear", { method: "POST" });
        if (res.ok) {
            loadDocumentList();
            checkSystemHealth();
        }
    } catch (err) {
        console.error("Clear database error:", err);
    }
}

/* Chatbot Form */
function initChatForm() {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const container = document.getElementById("chat-messages-container");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        appendMessage("user", text);
        input.value = "";

        const loadingMsg = appendMessage("bot", "Searching ChromaDB vectors & asking Gemini...");

        try {
            const res = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, top_k: 4 })
            });

            if (res.ok) {
                const data = await res.json();
                container.removeChild(loadingMsg);

                let botContent = data.answer;
                if (data.sources && data.sources.length) {
                    botContent += `<div class="sources-tag"><strong>Sources:</strong> ${data.sources.join(", ")}</div>`;
                }

                appendMessage("bot", botContent);
            } else {
                container.removeChild(loadingMsg);
                appendMessage("bot", "Error connecting to AI Assistant service.");
            }
        } catch (err) {
            container.removeChild(loadingMsg);
            appendMessage("bot", `Error: ${err.message}`);
        }
    });
}

function appendMessage(sender, htmlContent) {
    const container = document.getElementById("chat-messages-container");
    const div = document.createElement("div");
    div.className = `message ${sender === "user" ? "user-msg" : "bot-msg"}`;
    div.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid fa-${sender === "user" ? "user" : "robot"}"></i></div>
        <div class="msg-content"><p>${htmlContent}</p></div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

function sendPresetQuery(queryText) {
    document.getElementById("chat-input").value = queryText;
    document.getElementById("chat-form").dispatchEvent(new Event("submit"));
}

/* Vision & Camera Controls */
let webcamStream = null;
let webcamInterval = null;

function initCameraControls() {
    const btnWebcam = document.getElementById("btn-use-webcam");
    const btnSim = document.getElementById("btn-use-sim");
    const fileInput = document.getElementById("vision-file-input");

    btnWebcam.addEventListener("click", async () => {
        try {
            webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
            const video = document.getElementById("webcam-video");
            video.srcObject = webcamStream;
            video.style.display = "block";
            document.getElementById("vision-output-img").style.display = "none";
            
            // Update mode badges in UI
            updateCameraModeBadges(true);
            
            // Start periodic webcam analysis loop
            startWebcamLoop();
        } catch (err) {
            alert("Could not access camera device. Falling back to simulation mode.");
        }
    });

    btnSim.addEventListener("click", () => {
        stopWebcam();
        updateCameraModeBadges(false);
        triggerVisionAnalysis();
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
            const reader = new FileReader();
            reader.onload = (event) => {
                triggerVisionAnalysis(event.target.result);
            };
            reader.readAsDataURL(e.target.files[0]);
        }
    });

    // Initial frame trigger
    triggerVisionAnalysis();
}

function stopWebcam() {
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }
    if (webcamInterval) {
        clearInterval(webcamInterval);
        webcamInterval = null;
    }
    const video = document.getElementById("webcam-video");
    if (video) video.style.display = "none";
}

function startWebcamLoop() {
    if (webcamInterval) clearInterval(webcamInterval);
    // Initial immediate analysis
    const frame = captureWebcamFrame();
    triggerVisionAnalysis(frame);
    
    webcamInterval = setInterval(async () => {
        if (webcamStream && webcamStream.active) {
            const frame = captureWebcamFrame();
            if (frame) {
                await triggerVisionAnalysis(frame);
            }
        } else {
            stopWebcam();
        }
    }, 1500); // 1.5s interval
}

function captureWebcamFrame() {
    const video = document.getElementById("webcam-video");
    const canvas = document.getElementById("webcam-canvas");
    if (video && canvas && video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        return canvas.toDataURL("image/jpeg");
    }
    return "";
}

function updateCameraModeBadges(webcamActive) {
    const dashBadge = document.getElementById("dash-mode-badge");
    const camBadge = document.getElementById("camera-mode-badge");
    if (webcamActive) {
        if (dashBadge) {
            dashBadge.textContent = "Webcam Active";
            dashBadge.style.backgroundColor = "var(--success)";
        }
        if (camBadge) {
            camBadge.textContent = "Webcam Active";
            camBadge.style.backgroundColor = "var(--success)";
        }
    } else {
        if (dashBadge) {
            dashBadge.textContent = "Simulation Mode";
            dashBadge.style.backgroundColor = "var(--secondary)";
        }
        if (camBadge) {
            camBadge.textContent = "Simulation Mode";
            camBadge.style.backgroundColor = "var(--secondary)";
        }
    }
}

async function triggerVisionAnalysis(base64Image = "") {
    // Disable "Analyze Frame" buttons and show loading state
    const analyzeButtons = document.querySelectorAll("button[onclick='triggerVisionAnalysis()']");
    analyzeButtons.forEach(btn => {
        btn.disabled = true;
        btn.textContent = "Analyzing...";
    });

    try {
        // If empty image, check if webcam is active and try to capture
        if (!base64Image && webcamStream && webcamStream.active) {
            base64Image = captureWebcamFrame();
        }

        const res = await fetch("/vision/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image_b64: base64Image })
        });

        if (res.ok) {
            const data = await res.json();
            
            // Dashboard vision preview
            const dashImg = document.getElementById("dash-vision-img");
            const dashPlaceholder = document.getElementById("dash-vision-placeholder");
            if (data.annotated_image) {
                if (dashImg) {
                    dashImg.src = data.annotated_image;
                    dashImg.style.display = "block";
                }
                if (dashPlaceholder) {
                    dashPlaceholder.style.display = "none";
                }

                // Vision Tab Output
                const visImg = document.getElementById("vision-output-img");
                if (visImg) {
                    visImg.src = data.annotated_image;
                    visImg.style.display = "block";
                }
            }

            // Update Telemetry Displays
            const sceneDesc = document.getElementById("vision-scene-desc");
            if (sceneDesc) sceneDesc.textContent = data.scene_description || "Scene analyzed.";
            
            const visObs = document.getElementById("vis-obs");
            if (visObs) visObs.textContent = data.obstacle_detected ? "YES" : "NO";
            
            const visDir = document.getElementById("vis-dir");
            if (visDir) visDir.textContent = data.direction || "Front";
            
            const visDist = document.getElementById("vis-dist");
            if (visDist) {
                const isWebcam = webcamStream && webcamStream.active;
                if (isWebcam) {
                    visDist.textContent = "Estimated / Not available";
                } else {
                    visDist.textContent = `${data.distance_m} m`;
                }
            }
            
            const visConf = document.getElementById("vis-conf");
            if (visConf) visConf.textContent = `${Math.round((data.confidence || 0.9) * 100)}%`;

            // Update Navigation Decision
            updateNavigationTelemetry(data);
        }
    } catch (err) {
        console.error("Vision trigger error:", err);
    } finally {
        analyzeButtons.forEach(btn => {
            btn.disabled = false;
            btn.textContent = "Analyze Frame";
        });
    }
}

/* Navigation Telemetry Update */
async function updateNavigationTelemetry(visionData = null) {
    try {
        let res;
        if (visionData) {
            res = await fetch("/navigation/decision", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image_b64: "", sensor_telemetry: null })
            });
        } else {
            res = await fetch("/navigation/status");
        }

        if (res.ok) {
            const data = await res.json();
            renderNavigationData(data);
        }
    } catch (err) {
        console.error("Navigation telemetry error:", err);
    }
}

function renderNavigationData(data) {
    const actionBox = document.getElementById("dash-action-box");
    const action = data.decision || "MOVE FORWARD";

    if (actionBox) {
        actionBox.textContent = action;
        if (action === "STOP") {
            actionBox.style.background = "linear-gradient(135deg, #ef4444, #b91c1c)";
        } else {
            actionBox.style.background = "linear-gradient(135deg, var(--primary), var(--secondary))";
        }
    }

    const statAction = document.getElementById("stat-current-action");
    if (statAction) statAction.textContent = action;

    const safetyState = document.getElementById("stat-safety-state");
    if (safetyState) {
        if (action === "STOP") {
            safetyState.textContent = "EMERGENCY HALT";
            safetyState.className = "metric-value text-danger";
        } else {
            safetyState.textContent = "NOMINAL";
            safetyState.className = "metric-value green-text";
        }
    }

    const det = data.detected || {};
    const obsDetected = document.getElementById("dash-obs-detected");
    if (obsDetected) obsDetected.textContent = det.obstacle || "NO";
    
    const obsDir = document.getElementById("dash-obs-dir");
    if (obsDir) obsDir.textContent = det.direction || "Front";
    
    const obsConf = document.getElementById("dash-obs-conf");
    if (obsConf) obsConf.textContent = `${det.confidence_pct || 94}%`;
    
    const reasoningText = document.getElementById("dash-reasoning-text");
    if (reasoningText) reasoningText.textContent = data.reason || "Trajectory evaluated.";

    // Update Navigation Tab Decision Elements
    const navActionBox = document.getElementById("nav-action-box");
    if (navActionBox) {
        navActionBox.textContent = action;
        if (action === "STOP") {
            navActionBox.style.background = "linear-gradient(135deg, #ef4444, #b91c1c)";
        } else {
            navActionBox.style.background = "linear-gradient(135deg, var(--primary), var(--secondary))";
        }
    }

    const navSafetyState = document.getElementById("nav-safety-state");
    if (navSafetyState) {
        if (action === "STOP") {
            navSafetyState.textContent = "EMERGENCY HALT";
            navSafetyState.className = "text-danger";
            navSafetyState.style.fontWeight = "600";
        } else {
            navSafetyState.textContent = "NOMINAL";
            navSafetyState.className = "green-text";
            navSafetyState.style.fontWeight = "600";
        }
    }

    const navObsDir = document.getElementById("nav-obs-dir");
    if (navObsDir) navObsDir.textContent = det.direction || "Front";

    const navObsConf = document.getElementById("nav-obs-conf");
    if (navObsConf) navObsConf.textContent = `${det.confidence_pct || 94}%`;

    const navReasoningText = document.getElementById("nav-reasoning-text");
    if (navReasoningText) navReasoningText.textContent = data.reason || "Trajectory evaluated.";

    // Telemetry bars update
    const tele = data.telemetry || {};
    updateBar("lidar-front", tele.lidar_front_m || 2.8, 4.0);
    updateBar("lidar-left", tele.lidar_left_m || 2.5, 4.0);
    updateBar("lidar-right", tele.lidar_right_m || 0.9, 4.0);
}

function updateBar(barId, val, maxVal) {
    const fill = document.getElementById(`bar-${barId}`);
    const txt = document.getElementById(`txt-${barId}`);
    if (fill && txt) {
        const pct = Math.min(100, Math.max(5, (val / maxVal) * 100));
        fill.style.width = `${pct}%`;
        txt.textContent = `${val} m`;
    }
}

async function simulateObstacle(direction) {
    let sensorData = {
        lidar_front_m: 3.5,
        lidar_left_m: 2.8,
        lidar_right_m: 2.5
    };

    if (direction === 'Front') {
        sensorData = { lidar_front_m: 1.4, lidar_left_m: 2.8, lidar_right_m: 0.9 };
    } else if (direction === 'Left') {
        sensorData = { lidar_front_m: 3.2, lidar_left_m: 0.6, lidar_right_m: 2.8 };
    } else if (direction === 'Right') {
        sensorData = { lidar_front_m: 3.2, lidar_left_m: 2.8, lidar_right_m: 0.5 };
    } else if (direction === 'Clear') {
        sensorData = { lidar_front_m: 3.5, lidar_left_m: 2.8, lidar_right_m: 2.5 };
    }

    try {
        const res = await fetch("/navigation/decision", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                image_b64: "",
                sensor_telemetry: sensorData
            })
        });

        if (res.ok) {
            const data = await res.json();
            renderNavigationData(data);
        }
    } catch (err) {
        console.error("Simulate obstacle error:", err);
    }
}
