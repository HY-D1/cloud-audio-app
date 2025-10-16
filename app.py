
import os
import uuid
import time
import threading
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, jsonify, send_from_directory, Response, send_file

app = Flask(__name__, static_folder="static", static_url_path="")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(BASE_DIR, "storage")
UPLOADS = os.path.join(STORE, "uploads")
OUTPUTS = os.path.join(STORE, "outputs")
os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(OUTPUTS, exist_ok=True)

def _write_captions(job_id: str):
    """Simulate processing delay and write demo caption files."""
    out_dir = os.path.join(OUTPUTS, job_id)
    os.makedirs(out_dir, exist_ok=True)
    # Simple demo .vtt/.srt/.lrc content
    vtt = "WEBVTT\n\n1\n00:00:00.000 --> 00:00:02.000\nHello from the local demo!\n"
    srt = "1\n00:00:00,000 --> 00:00:02,000\nHello from the local demo!\n"
    lrc = "[00:00.00] Hello from the local demo!\n"
    with open(os.path.join(out_dir, "captions.vtt"), "w", encoding="utf-8") as f:
        f.write(vtt)
    with open(os.path.join(out_dir, "captions.srt"), "w", encoding="utf-8") as f:
        f.write(srt)
    with open(os.path.join(out_dir, "captions.lrc"), "w", encoding="utf-8") as f:
        f.write(lrc)
    with open(os.path.join(out_dir, "status.json"), "w", encoding="utf-8") as f:
        f.write('{"state":"COMPLETED"}')

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/presign", methods=["GET"])
def presign():
    filename = request.args.get("filename", "audio.wav")
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "wav").lower()
    job_id = str(uuid.uuid4())
    key = f"uploads/{job_id}.{ext}"
    # In a real system this would be an S3 presigned URL. Here it's our local upload endpoint.
    upload_url = f"/upload?key={key}"
    return jsonify({"jobId": job_id, "uploadUrl": upload_url, "s3Key": key})

@app.route("/upload", methods=["PUT","POST"])
def upload():
    # Accept raw body (PUT) or form file (POST).
    key = request.args.get("key")
    if not key:
        return Response("missing key", status=400)
    dest_path = os.path.join(STORE, key)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if request.method == "PUT":
        data = request.get_data()
        with open(dest_path, "wb") as f:
            f.write(data)
    else:
        if "file" not in request.files:
            return Response("missing file", status=400)
        file = request.files["file"]
        file.save(dest_path)
    # Derive job_id
    base = os.path.basename(dest_path)
    job_id = base.split(".")[0]
    # Simulate async processing with a short delay
    def worker():
        time.sleep(2)
        _write_captions(job_id)
    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok": True, "jobId": job_id})

@app.route("/check", methods=["GET"])
def check():
    job_id = request.args.get("jobId")
    if not job_id:
        return Response("missing jobId", status=400)
    out_dir = os.path.join(OUTPUTS, job_id)
    status_path = os.path.join(out_dir, "status.json")
    if not os.path.exists(status_path):
        return jsonify({"state": "PENDING"})
    # Generate local download URLs
    urls = []
    for ext in ["vtt","srt","lrc"]:
        path = os.path.join(out_dir, f"captions.{ext}")
        if os.path.exists(path):
            urls.append({"kind": ext.upper(), "url": f"/download/{job_id}/captions.{ext}"})
    return jsonify({"state":"COMPLETED", "urls": urls})

@app.route("/download/<job_id>/<path:filename>", methods=["GET"])
def download(job_id, filename):
    out_dir = os.path.join(OUTPUTS, job_id)
    if not os.path.exists(os.path.join(out_dir, filename)):
        return Response("not found", status=404)
    return send_from_directory(out_dir, filename, as_attachment=False)

# Serve static files (index.html, app.js, styles.css)
@app.route("/static/<path:fname>")
def static_files(fname):
    return send_from_directory(app.static_folder, fname)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
