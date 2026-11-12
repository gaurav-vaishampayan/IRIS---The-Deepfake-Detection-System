// Update the port if your backend runs on 5000 instead of FastAPI's default 8000
const API = "http://127.0.0.1:8000";

async function request(path, options = {}) {
    const res = await fetch(API + path, options);
    if (!res.ok) {
        const errorText = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}${errorText ? `: ${errorText}` : ""}`);
    }
    return res.json();
}

document.addEventListener("DOMContentLoaded", () => {
    // =========================================================
    // 1. DEEPFAKE DETECTION UPLOAD (runs only on pages/main.html)
    // =========================================================
    const uploadForm = document.getElementById("upload-form");
    const dropzone = document.getElementById("dropzone");
    const videoInput = document.getElementById("video");
    const fileNameDisplay = document.getElementById("file-name");
    const uploadBtn = document.getElementById("upload-btn");
    const resultsSection = document.getElementById("results");
    const verdictOutput = document.getElementById("verdict");
    const confidenceOutput = document.getElementById("confidence-graph");

    if (uploadForm && videoInput) {
        const updateSelectedFile = (file) => {
            if (file) {
                fileNameDisplay.textContent = file.name;
                uploadBtn.disabled = false;
            } else {
                fileNameDisplay.textContent = "";
                uploadBtn.disabled = true;
            }
        };

        // File picker selection
        videoInput.addEventListener("change", () => {
            updateSelectedFile(videoInput.files[0]);
        });

        // Drag-and-drop support on the dropzone label
        if (dropzone) {
            dropzone.addEventListener("dragover", (e) => {
                e.preventDefault();
                dropzone.classList.add("drag-over");
            });

            dropzone.addEventListener("dragleave", () => {
                dropzone.classList.remove("drag-over");
            });

            dropzone.addEventListener("drop", (e) => {
                e.preventDefault();
                dropzone.classList.remove("drag-over");

                const droppedFiles = e.dataTransfer.files;
                if (droppedFiles.length > 0) {
                    videoInput.files = droppedFiles;
                    updateSelectedFile(droppedFiles[0]);
                }
            });
        }

        // Submit video to backend API
        uploadForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const file = videoInput.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append("video", file);

            uploadBtn.disabled = true;
            uploadBtn.textContent = "Analyzing...";
            resultsSection.hidden = false;
            verdictOutput.textContent = "Extracting frames and analyzing facial features...";
            confidenceOutput.textContent = "Waiting for model scores...";

            try {
                // Ensure "/predict" matches your FastAPI @app.post(...) route
                const data = await request("/predict", {
                    method: "POST",
                    body: formData,
                });

                const verdict = data.verdict || data.prediction || "Analysis Complete";
                const confidence =
                    data.confidence !== undefined
                        ? ` (${(Number(data.confidence) * 100).toFixed(1)}% confidence)`
                        : "";

                verdictOutput.textContent = `${verdict}${confidence}`;

                if (Array.isArray(data.frame_scores) && data.frame_scores.length > 0) {
                    confidenceOutput.textContent =
                        "Per-frame scores: " +
                        data.frame_scores.map((s) => Number(s).toFixed(2)).join(", ");
                } else if (data.message) {
                    confidenceOutput.textContent = data.message;
                } else {
                    confidenceOutput.textContent = "Frame-level analysis completed.";
                }
            } catch (err) {
                console.error("Detection request failed:", err);
                verdictOutput.textContent =
                    "Could not connect to backend. Verify that the API server is running.";
                confidenceOutput.textContent = "No frame data available.";
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.textContent = "Upload";
            }
        });
    }

    // =========================================================
    // 2. SPOT-THE-REAL-ONE QUIZ (runs only on index.html)
    // =========================================================
    const quizRound = document.getElementById("quiz-round");
    const quizCorrect = document.getElementById("quiz-correct");
    const quizWrong = document.getElementById("quiz-wrong");
    const quizNext = document.getElementById("quiz-next");

    if (quizRound) {
        const quizCards = quizRound.querySelectorAll(".quiz-card");
        const quizDetectLink = document.querySelector("#quiz a[href*='main.html']");

        quizCards.forEach((card) => {
            card.addEventListener("click", () => {
                const isReal = card.dataset.correct === "true";

                quizCards.forEach((btn) => {
                    btn.disabled = true;
                });

                quizCorrect.hidden = !isReal;
                quizWrong.hidden = isReal;
                quizNext.hidden = false;
                if (quizDetectLink) quizDetectLink.hidden = false;
            });
        });

        if (quizNext) {
            quizNext.addEventListener("click", () => {
                quizCards.forEach((btn) => {
                    btn.disabled = false;
                });
                quizCorrect.hidden = true;
                quizWrong.hidden = true;
                quizNext.hidden = true;
            });
        }
    }
});