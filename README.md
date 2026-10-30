# IRIS---The-Deepfake-Detection-System
IRIS is a state of the art deepfake detection system,using CNN and LSTM architecture to identify manipulative content and synthetic media.

## KEY FEATURES

- Frame by Frame Analysis
- Deep Learning Core
- Confidence Scoring
- Web Interface

IRIS is a hybrid spatial-temporal detector. The spatial branch checks each face crop for synthesis errors such as blurred jawline boundaries, checkerboard artifacts and mismatched lighting. The temporal branch monitors consecutive frames to confirm that lip-sync and eye movement follow natural human mechanics. The output is a manipulation probability score plus a heatmap of the altered regions. To optimise performance, the system ignores background data and focuses entirely on the subject's face, which also stops the model learning background shortcuts.

System architecture
1. Input: the user uploads an image or video through the web interface.
2. Preprocessing: the backend extracts frames at a set FPS and isolates facial regions with face detection. Crops are expanded slightly and resized (for example, 224×224). Frames with no detected face are skipped and counted.
3. Inference: cropped faces are fed into the pretrained deep learning model (spatial branch per frame, temporal branch over the frame sequence).
4. Aggregation: per-frame confidence scores are combined (mean, trimmed mean or top-k mean) into a final classification.
5. Output: the backend returns the Real/Fake verdict, the confidence, a per-frame score plot and visual heatmaps.