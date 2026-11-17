const API = window.location.origin.startsWith("http")
    ? window.location.origin
    : "http://127.0.0.1:8000";

async function request(path, options = {}) {
    const res = await fetch(API + path, options);
    if (!res.ok) {
        const errorText = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}${errorText ? `: ${errorText}` : ""}`);
    }
    return res.json();
}

document.addEventListener("DOMContentLoaded", () => {
    const uploadForm = document.getElementById("upload-form");
    const dropzone = document.getElementById("dropzone");
    const videoInput = document.getElementById("video");
    const fileNameDisplay = document.getElementById("file-name");
    const uploadBtn = document.getElementById("upload-btn");
    const resultsSection = document.getElementById("results");
    const verdictOutput = document.getElementById("verdict");
    const confidenceOutput = document.getElementById("confidence-graph");

    const posterPrompt = document.getElementById("poster-prompt");
    const btnGeneratePoster = document.getElementById("btn-generate-poster");
    const btnSkipPoster = document.getElementById("btn-skip-poster");
    const posterStatus = document.getElementById("poster-status");

    let currentAnalysisId = null;

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

        videoInput.addEventListener("change", () => {
            updateSelectedFile(videoInput.files[0]);
        });

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

        uploadForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const file = videoInput.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append("video", file);

            uploadBtn.disabled = true;
            uploadBtn.textContent = "Analyzing...";
            resultsSection.hidden = false;
            if (posterPrompt) posterPrompt.hidden = true;
            verdictOutput.textContent = "Extracting frames and analyzing facial features...";
            confidenceOutput.textContent = "Waiting for model scores...";

            try {
                const data = await request("/predict", {
                    method: "POST",
                    body: formData,
                });

                currentAnalysisId = data.analysis_id;

                const verdict = data.verdict || data.prediction || "Analysis Complete";
                const confidence =
                    data.confidence !== undefined
                        ? ` (${(Number(data.confidence) * 100).toFixed(1)}% confidence)`
                        : "";

                verdictOutput.textContent = `${verdict}${confidence}`;
                resultsSection.scrollIntoView({ behavior: "smooth" });

                if (Array.isArray(data.frame_scores) && data.frame_scores.length > 0) {
                    confidenceOutput.textContent =
                        "Per-frame scores: " +
                        data.frame_scores.map((s) => Number(s).toFixed(2)).join(", ");
                } else if (data.message) {
                    confidenceOutput.textContent = data.message;
                } else {
                    confidenceOutput.textContent = "Frame-level analysis completed.";
                }

                if (posterPrompt && currentAnalysisId) {
                    posterPrompt.hidden = false;
                    posterStatus.textContent = "";
                    btnGeneratePoster.disabled = false;
                    btnGeneratePoster.textContent = "Yes, Generate Poster";
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

        if (btnGeneratePoster) {
            btnGeneratePoster.addEventListener("click", async () => {
                if (!currentAnalysisId) return;

                btnGeneratePoster.disabled = true;
                btnGeneratePoster.textContent = "Generating...";
                posterStatus.textContent = "Creating poster with first frame and QR code...";

                try {
                    await request("/generate-poster", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ analysis_id: currentAnalysisId }),
                    });
                    window.location.href = `./poster.html?id=${encodeURIComponent(currentAnalysisId)}`;
                } catch (err) {
                    console.error("Poster generation failed:", err);
                    posterStatus.textContent = "Could not generate poster. Please try again.";
                    btnGeneratePoster.disabled = false;
                    btnGeneratePoster.textContent = "Yes, Generate Poster";
                }
            });
        }

        if (btnSkipPoster) {
            btnSkipPoster.addEventListener("click", () => {
                posterPrompt.hidden = true;
            });
        }
    }
});