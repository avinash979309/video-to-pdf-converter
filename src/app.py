import os
from flask import Flask, request, send_file, render_template
from fpdf import FPDF
from moviepy.editor import VideoFileClip
import mimetypes

app = Flask(__name__)

# Define the path for uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'src', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def is_video_file(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type and mime_type.startswith('video')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video = request.files['video']
        fps = int(request.form.get('fps', 20))  # Default to 20 FPS if not provided

        if fps <= 0:
            return "FPS must be greater than 0", 400

        video_filename = video.filename
        video_path = os.path.join(UPLOAD_FOLDER, video_filename)
        video.save(video_path)

        if not is_video_file(video_path):
            return "Uploaded file is not a valid video", 400

        pdf_filename = os.path.splitext(video_filename)[0] + ".pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)

        create_pdf_from_video(video_path, pdf_path, fps)

        return render_template('result.html', pdf_filename=pdf_filename)

    return render_template('index.html')

def create_pdf_from_video(video_path, pdf_path, fps):
    clip = VideoFileClip(video_path)
    pdf = FPDF()

    # Calculate interval between frames
    interval = clip.duration / fps

    # Ensure the interval isn't zero or impractically small
    if interval < 0.001:
        raise ValueError("Interval too small, resulting in zero when converting to integer.")

    frame_times = [t for t in range(0, int(clip.duration), int(interval))]

    if not frame_times:
        frame_times = [0]  # Capture at least the first frame if duration is very short

    for t in frame_times:
        frame_path = os.path.join(UPLOAD_FOLDER, f"frame_{t}.jpg")
        clip.save_frame(frame_path, t)
        pdf.add_page()
        pdf.image(frame_path, x=0, y=0, w=210, h=297)  # A4 size
        os.remove(frame_path)

    pdf.output(pdf_path)

@app.route('/view/<filename>', methods=['GET'])
def view_file(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.isfile(path):
        return send_file(path, as_attachment=False)
    return "File not found", 404

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.isfile(path):
        return send_file(path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)
