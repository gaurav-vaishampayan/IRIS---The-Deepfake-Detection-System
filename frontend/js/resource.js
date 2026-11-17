console.log("IRIS resources.js active");

const IMAGE_POOL = [
  "../assets/images/pexels-merlin-14314636.jpg"
];

const FALLBACK_RESOURCES = {
  news: [
    { title: "Global Regulators Enforce Mandatory Watermarking for Synthetic AI Video", url: "https://c2pa.org/", source: "Tech News", date: "2026" },
    { title: "Real-Time Voice & Face Cloning Surge in Enterprise KYC Fraud", url: "https://www.wired.com/category/security/", source: "Security", date: "2026" },
    { title: "Hardware-Level Camera Signing Gains Native Mobile Support", url: "https://www.theverge.com/", source: "Mobile", date: "2026" },
    { title: "Open-Source Benchmarks Expose Generalization Gaps in Detectors", url: "https://spectrum.ieee.org/", source: "IEEE", date: "2026" },
    { title: "Digital Forensics Taskforces Adopt Multimodal Audio-Visual Checks", url: "https://arstechnica.com/", source: "Forensics", date: "2026" }
  ],
  research: [
    { title: "FaceForensics++: Learning to Detect Manipulated Facial Images", url: "https://arxiv.org/abs/1901.08971", source: "arXiv", date: "ICCV" },
    { title: "DFDC: The DeepFake Detection Challenge Dataset", url: "https://arxiv.org/abs/2006.07397", source: "arXiv", date: "Meta AI" },
    { title: "Self-Blended Images (SBI) for Generalizable Deepfake Detection", url: "https://arxiv.org/abs/2204.08376", source: "arXiv", date: "CVPR" },
    { title: "Universal Fake Image Detectors via Vision Transformer Feature Spaces", url: "https://arxiv.org/abs/2302.10174", source: "arXiv", date: "CVPR" },
    { title: "Celeb-DF: A Large-Scale Challenging Dataset for DeepFake Forensics", url: "https://arxiv.org/abs/1909.12962", source: "arXiv", date: "CVPR" }
  ],
  blogs: [
    { title: "How Grad-CAM Visualizes Facial Manipulation Artifacts", url: "https://arxiv.org/abs/1610.02391", source: "Engineering", date: "Guide" },
    { title: "Spatial vs. Frequency Domain Analysis in Deepfake Detection", url: "https://distill.pub/", source: "Vision", date: "Deep Dive" },
    { title: "5 Visual Clues to Spot AI-Generated Faces Manually", url: "https://www.mediaforensics.org/", source: "Literacy", date: "Article" },
    { title: "Why Social Media Video Compression Degrades Detector Accuracy", url: "https://paperswithcode.com/task/deepfake-detection", source: "ML Ops", date: "Note" },
    { title: "Cryptographic Verification Posters with QR Provenance", url: "https://c2pa.org/", source: "IRIS", date: "Architecture" }
  ],
  "case-studies": [
    { title: "$25M Multinational CFO Video Call Deepfake Heist", url: "https://www.cnn.com/2024/02/04/asia/deepfake-cfo-scam-hong-kong-intl-hnk/index.html", source: "Case #01", date: "Finance" },
    { title: "Synthetic Audio Robocalls Targeting Primary Voters", url: "https://www.fcc.gov/", source: "Case #02", date: "Policy" },
    { title: "Celebrity Likeness Impersonation in Investment Scams", url: "https://www.ftc.gov/", source: "Case #03", date: "Media" },
    { title: "Bypassing Remote Onboarding KYC with Virtual Camera Injection", url: "https://owasp.org/", source: "Case #04", date: "Security" },
    { title: "Journalistic Verification of Conflict-Zone Synthetic Media", url: "https://firstdraftnews.org/", source: "Case #05", date: "OSINT" }
  ]
};

function pickRandom(items, count = 5) {
  const arr = [...items];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr.slice(0, count);
}

async function fetchLiveHN(query, label, fallbackKey) {
  const url = `https://hn.algolia.com/api/v1/search?query=${encodeURIComponent(query)}&tags=story&hitsPerPage=30`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("HN fetch failed");

  const data = await res.json();
  const validHits = (data.hits || [])
    .filter(hit => hit.url && hit.title)
    .map(hit => ({
      title: hit.title,
      url: hit.url,
      source: label,
      date: hit.created_at ? hit.created_at.slice(0, 10) : "2026"
    }));

  return validHits.length >= 5 ? pickRandom(validHits, 5) : pickRandom(FALLBACK_RESOURCES[fallbackKey], 5);
}

function populateSection(sectionId, items) {
  const section = document.getElementById(sectionId);
  if (!section || !items.length) return;

  const mainImg = section.querySelector(".main-card img");
  const mainLink = section.querySelector(".main-card a");
  if (mainImg && items[0]) {
    mainImg.src = IMAGE_POOL[Math.floor(Math.random() * IMAGE_POOL.length)];
    mainImg.alt = items[0].title;
  }
  if (mainLink && items[0]) {
    mainLink.href = items[0].url;
    mainLink.target = "_blank";
    mainLink.rel = "noopener noreferrer";
    mainLink.textContent = items[0].title;
  }

  const secondaryCards = section.querySelectorAll(".secondary-cards");
  secondaryCards.forEach((card, idx) => {
    const img = card.querySelector("img");
    const link = card.querySelector("a");
    const item = items[idx + 1];
    if (!item) return;

    if (img) {
      img.src = IMAGE_POOL[Math.floor(Math.random() * IMAGE_POOL.length)];
      img.alt = item.title;
    }
    if (link) {
      link.href = item.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = item.title;
    }
  });
}

async function initResources() {
  const sectionIds = ["news", "research", "blogs", "case-studies"];

  // 1. Immediately populate shuffled curated items so placeholders disappear right away
  sectionIds.forEach(id => populateSection(id, pickRandom(FALLBACK_RESOURCES[id], 5)));

  // 2. Fetch live stories from Hacker News Algolia API (supports CORS in all browsers)
  const results = await Promise.allSettled([
    fetchLiveHN("deepfake", "News", "news"),
    fetchLiveHN("deepfake detection paper arxiv", "Research", "research"),
    fetchLiveHN("computer vision forensics synthetic media", "Blog", "blogs"),
    fetchLiveHN("deepfake scam impersonation fraud", "Case Study", "case-studies")
  ]);

  results.forEach((result, i) => {
    if (result.status === "fulfilled") {
      populateSection(sectionIds[i], result.value);
    }
  });
}

initResources();