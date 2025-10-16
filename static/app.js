
const statusEl = document.getElementById("status");
const linksEl  = document.getElementById("links");

document.getElementById("upload").onclick = async () => {
  const f = document.getElementById("file").files[0];
  if (!f) { alert("Pick an audio file."); return; }
  statusEl.textContent = "Requesting upload URL…";
  const pres = await fetch(`/presign?filename=${encodeURIComponent(f.name)}&type=${encodeURIComponent(f.type)}`).then(r=>r.json());
  // PUT raw body to local /upload endpoint
  await fetch(pres.uploadUrl, { method:"PUT", body: f });
  statusEl.textContent = "Uploaded. Processing…";
  let delay = 1000;
  const poll = async () => {
    const res = await fetch(`/check?jobId=${pres.jobId}`).then(r=>r.json());
    if (res.state === "COMPLETED") {
      statusEl.textContent = "Done ✓";
      linksEl.innerHTML = res.urls.map(u => `<p><a href="${u.url}" target="_blank">${u.kind}</a></p>`).join("");
    } else {
      statusEl.textContent = "Still processing…";
      setTimeout(poll, delay);
      delay = Math.min(delay + 500, 5000);
    }
  };
  poll();
};
