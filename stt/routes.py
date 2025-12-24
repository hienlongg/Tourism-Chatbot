from flask import Blueprint, request, jsonify
import assemblyai as aai
import os
import tempfile

speech_bp = Blueprint("speech_to_text", __name__)

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")


@speech_bp.route("/api/speech-to-text", methods=["POST"])
def speech_to_text():
    if "audio" not in request.files:
        return jsonify({"success": False, "error": {"message": "No audio file"}}), 400

    audio_file = request.files["audio"]

    fd, tmp_path = tempfile.mkstemp(suffix=".webm")
    os.close(fd)

    try:
        audio_file.save(tmp_path)

        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(tmp_path)

        if transcript.status == aai.TranscriptStatus.error:
            return jsonify({
                "success": False,
                "error": {"message": transcript.error}
            }), 500

        return jsonify({
            "success": True,
            "data": {
                "text": transcript.text
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "STT_INTERNAL_ERROR",
                "message": str(e)
            }
        }), 500

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
