const API = "http://localhost:5000";
const output = document.getElementById("output");

async function request(path, options) {
  const res = await fetch(API + path, options);
  if (!res.ok) throw new Error(res.status);
  return res.json();
}

document.getElementById("getBtn").onclick = async () => {
  try {
    const { message } = await request("/api/data");
    output.textContent = message;
  } catch {
    output.textContent = "Could not connect to backend";
  }
};

document.getElementById("sendBtn").onclick = async () => {
  const name = document.getElementById("nameInput").value;
  try {
    const { received } = await request("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    output.textContent = "Server received: " + received;
  } catch {
    output.textContent = "Could not connect to backend";
  }
};