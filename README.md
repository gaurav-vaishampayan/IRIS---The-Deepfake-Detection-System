# IRIS---The-Deepfake-Detection-System
IRIS is a state of the art deepfake detection system,using CNN and LSTM architecture to identify manipulative content and synthetic media.

## KEY FEATURES

- Frame by Frame Analysis
- Deep Learning Core
- Confidence Scoring
- Web Interface

IRIS is a hybrid spatial-temporal detector. The spatial branch checks each face crop for synthesis errors such as blurred jawline boundaries, checkerboard artifacts and mismatched lighting. The temporal branch monitors consecutive frames to confirm that lip-sync and eye movement follow natural human mechanics. The output is a manipulation probability score plus a heatmap of the altered regions. To optimise performance, the system ignores background data and focuses entirely on the subject's face, which also stops the model learning background shortcuts.

##System architecture
1. Input: the user uploads an image or video through the web interface.
2. Preprocessing: the backend extracts frames at a set FPS and isolates facial regions with face detection. Crops are expanded slightly and resized (for example, 224×224). Frames with no detected face are skipped and counted.
3. Inference: cropped faces are fed into the pretrained deep learning model (spatial branch per frame, temporal branch over the frame sequence).
4. Aggregation: per-frame confidence scores are combined (mean, trimmed mean or top-k mean) into a final classification.
5. Output: the backend returns the Real/Fake verdict, the confidence, a per-frame score plot.

##Objectives
•	Build a binary classifier (real vs. fake) for face images and video using transfer learning on a pretrained CNN or transformer backbone.
•	Implement a full pipeline: frame extraction, face detection and cropping, per-frame inference, score aggregation and verdict.
•	Evaluate with AUC, precision, recall, F1 and a confusion matrix, using video-level data splits to prevent leakage.
•	Deliver a web interface that accepts an uploaded video or image and returns the verdict, score and heatmap.
•	Measure cross-dataset generalization (train on one dataset, test on another) and report the drop.
•	Compare against existing tools and published baselines, and document limitations and ethical considerations.


