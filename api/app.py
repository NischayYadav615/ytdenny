from flask import Flask, render_template, request, jsonify
from pytube import YouTube
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Temporary directory for Vercel (using /tmp to store downloads)
DOWNLOAD_FOLDER = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/check", methods=["POST"])
def check_video():
    """Fetch video details and quality options."""
    try:
        url = request.json.get("url")
        yt = YouTube(url)

        # Check if the video is live
        if yt.length == 0:
            return jsonify({"error": "Live videos are not supported at this time."})

        # Fetch available streams
        streams = yt.streams.filter(file_extension="mp4")
        quality_options = [
            {
                "itag": stream.itag,
                "resolution": stream.resolution,
                "type": "video" if stream.includes_video_track else "audio",
                "has_audio": stream.includes_audio_track,
                "url": stream.url,
            }
            for stream in streams
        ]

        return jsonify({
            "title": yt.title,
            "thumbnail": yt.thumbnail_url,
            "qualities": quality_options,
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/download", methods=["POST"])
def download_video():
    """Download the selected stream."""
    try:
        url = request.json.get("url")
        itag = request.json.get("itag")
        filename = request.json.get("filename")

        yt = YouTube(url)
        stream = yt.streams.get_by_itag(itag)

        # Generating safe filename
        safe_filename = secure_filename(f"{filename}.{stream.subtype}")
        filepath = os.path.join(DOWNLOAD_FOLDER, safe_filename)

        # Download the stream
        stream.download(output_path=DOWNLOAD_FOLDER, filename=safe_filename)

        return jsonify({"filepath": filepath, "filename": safe_filename})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/download-file/<filename>")
def download_file(filename):
    """Serve the downloaded file."""
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
            
