import os
import base64
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_BASE_URL = "https://api.minimax.io"
VIDEO_MODEL = "MiniMax-H3"


HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MIKAI AI</title>

<style>
body{
    margin:0;
    background:#0b0b12;
    color:#eee;
    font-family:Arial,sans-serif;
}

.wrap{
    max-width:900px;
    margin:30px auto;
    padding:20px;
}

.card{
    background:#151521;
    border:1px solid #303044;
    border-radius:16px;
    padding:22px;
}

h1{
    margin-top:0;
}

label{
    display:block;
    margin:16px 0 8px;
    font-weight:bold;
}

input,textarea,select{
    width:100%;
    box-sizing:border-box;
    background:#0d0d15;
    color:#fff;
    border:1px solid #44445a;
    border-radius:9px;
    padding:12px;
}

textarea{
    min-height:150px;
    resize:vertical;
}

button{
    margin-top:18px;
    width:100%;
    padding:14px;
    border:0;
    border-radius:10px;
    background:#8b3dff;
    color:#fff;
    font-weight:bold;
    font-size:16px;
    cursor:pointer;
}

button:disabled{
    opacity:.5;
}

.preview{
    max-width:100%;
    max-height:500px;
    display:none;
    margin-top:15px;
    border-radius:10px;
}

.status{
    margin-top:18px;
    padding:12px;
    border-radius:9px;
    background:#0d0d15;
    white-space:pre-wrap;
}

video{
    width:100%;
    margin-top:18px;
    border-radius:10px;
    background:#000;
    display:none;
}

.small{
    color:#aaa;
    font-size:13px;
}
</style>
</head>

<body>

<div class="wrap">

<div class="card">

<h1>🎬 MIKAI AI</h1>

<div class="small">
MiniMax H3 Image-to-Video • Direct API
</div>

<label>Upload Image</label>

<input
    id="image"
    type="file"
    accept="image/png,image/jpeg,image/webp,image/heic,image/heif"
>

<img id="preview" class="preview">


<label>Video Prompt</label>

<textarea
    id="prompt"
    placeholder="Describe how you want the image to move..."
>A Filipino man stands naturally and looks toward the camera. Subtle realistic body movement, natural blinking and breathing, gentle clothing movement, cinematic camera push-in, realistic lighting, smooth motion, realistic human physics. No BGM. Natural SFX only.</textarea>


<label>Duration</label>

<select id="duration">

<option value="4">4 seconds</option>
<option value="5">5 seconds</option>
<option value="6">6 seconds</option>
<option value="7">7 seconds</option>
<option value="8">8 seconds</option>
<option value="9">9 seconds</option>
<option value="10" selected>10 seconds</option>
<option value="11">11 seconds</option>
<option value="12">12 seconds</option>
<option value="13">13 seconds</option>
<option value="14">14 seconds</option>
<option value="15">15 seconds</option>

</select>


<label>Resolution</label>

<select id="resolution">

<option value="768P" selected>768P</option>
<option value="2K">2K</option>

</select>


<button id="generate">
✨ Generate Video
</button>


<div id="status" class="status">
Ready.
</div>


<video
    id="video"
    controls
    playsinline
></video>

</div>
</div>


<script>

const imageInput = document.getElementById("image");

const preview = document.getElementById("preview");

const generate = document.getElementById("generate");

const statusBox = document.getElementById("status");

const video = document.getElementById("video");


imageInput.addEventListener("change", () => {

    const file = imageInput.files[0];

    if (!file) return;

    preview.src = URL.createObjectURL(file);

    preview.style.display = "block";

    video.style.display = "none";

    statusBox.textContent = "Image ready.";

});


function setStatus(text){

    statusBox.textContent = text;

}


generate.addEventListener("click", async () => {

    const file = imageInput.files[0];

    const prompt =
        document.getElementById("prompt").value.trim();

    const duration =
        document.getElementById("duration").value;

    const resolution =
        document.getElementById("resolution").value;


    if (!file) {

        setStatus("❌ Please upload an image first.");

        return;

    }


    if (!prompt) {

        setStatus("❌ Please enter a video prompt.");

        return;

    }


    generate.disabled = true;

    video.style.display = "none";

    setStatus("⏳ Sending image to MiniMax...");


    try {

        const form = new FormData();

        form.append("image", file);

        form.append("prompt", prompt);

        form.append("duration", duration);

        form.append("resolution", resolution);


        const res = await fetch(
            "/generate",
            {
                method:"POST",
                body:form
            }
        );


        const data = await res.json();


        if (!res.ok) {

            throw new Error(
                data.error || "Generation request failed."
            );

        }


        const taskId = data.task_id;


        setStatus(
            "⏳ MiniMax task created.\n" +
            "Waiting for video...\n\n" +
            "Task ID: " + taskId
        );


        while (true) {

            await new Promise(
                r => setTimeout(r,5000)
            );


            const sres = await fetch(
                "/status/" +
                encodeURIComponent(taskId)
            );


            const sdata = await sres.json();


            if (!sres.ok) {

                throw new Error(
                    sdata.error ||
                    "Status check failed."
                );

            }


            if (
                sdata.status === "queued" ||
                sdata.status === "running"
            ) {

                setStatus(
                    "⏳ Generating video...\n" +
                    "Status: " +
                    sdata.status
                );

                continue;

            }


            if (sdata.status === "succeeded") {

                video.src = sdata.video_url;

                video.style.display = "block";

                video.load();

                setStatus(
                    "✅ Video generated successfully."
                );

                break;

            }


            throw new Error(
                "MiniMax generation failed." +
                (
                    sdata.error
                    ?
                    "\nCode: " +
                    (sdata.error.code || "") +
                    "\n" +
                    (sdata.error.message || "")
                    :
                    ""
                )
            );

        }


    } catch (err) {

        setStatus(
            "❌ " + err.message
        );

    } finally {

        generate.disabled = false;

    }

});

</script>

</body>
</html>
"""


def api_headers():

    if not MINIMAX_API_KEY:

        raise RuntimeError(
            "MINIMAX_API_KEY is not configured on the server."
        )

    return {
        "Authorization":
            f"Bearer {MINIMAX_API_KEY}",

        "Content-Type":
            "application/json",
    }


def get_image_data_url(file_storage):

    raw = file_storage.read()

    if not raw:

        raise ValueError(
            "The uploaded image is empty."
        )


    if len(raw) > 30 * 1024 * 1024:

        raise ValueError(
            "Image is larger than 30 MB."
        )


    content_type = (
        file_storage.mimetype or
        "image/jpeg"
    ).lower()


    allowed = {

        "image/jpeg": "jpeg",

        "image/jpg": "jpeg",

        "image/png": "png",

        "image/webp": "webp",

        "image/heic": "heic",

        "image/heif": "heif",

    }


    if content_type not in allowed:

        raise ValueError(
            "Unsupported image format. "
            "Use JPG, PNG, or WebP."
        )


    encoded = base64.b64encode(
        raw
    ).decode("ascii")


    return (
        "data:image/" +
        allowed[content_type] +
        ";base64," +
        encoded
    )


@app.get("/")
def home():

    return render_template_string(HTML)


@app.get("/health")
def health():

    return jsonify({

        "ok": True,

        "minimax_key_configured":
            bool(MINIMAX_API_KEY)

    })


@app.post("/generate")
def generate_video():

    try:

        image = request.files.get("image")

        prompt = (
            request.form.get("prompt") or ""
        ).strip()


        duration = int(
            request.form.get("duration") or "10"
        )


        resolution = (
            request.form.get("resolution") or
            "768P"
        ).upper()


        if not image:

            return jsonify({
                "error":
                    "No image was uploaded."
            }), 400


        if not prompt:

            return jsonify({
                "error":
                    "Video prompt is required."
            }), 400


        if len(prompt) > 7000:

            return jsonify({
                "error":
                    "Prompt is too long. "
                    "Maximum is 7000 characters."
            }), 400


        if duration < 4 or duration > 15:

            return jsonify({
                "error":
                    "Duration must be "
                    "between 4 and 15 seconds."
            }), 400


        if resolution not in (
            "768P",
            "2K"
        ):

            return jsonify({
                "error":
                    "Resolution must be "
                    "768P or 2K."
            }), 400


        image_url = get_image_data_url(
            image
        )


        payload = {

            "model":
                VIDEO_MODEL,


            "content": [

                {
                    "type": "text",

                    "text": prompt
                },

                {
                    "type": "image_url",

                    "image_url": {

                        "url": image_url

                    },

                    "role":
                        "first_frame"

                }

            ],


            "resolution":
                resolution,


            "duration":
                duration,


            "ratio":
                "adaptive"

        }


        response = requests.post(

            f"{MINIMAX_BASE_URL}"
            "/v2/video_generation",

            headers=api_headers(),

            json=payload,

            timeout=120

        )


        try:

            data = response.json()

        except Exception:

            data = {
                "raw":
                    response.text
            }


        if response.status_code >= 400:

            return jsonify({

                "error":
                    f"MiniMax API error "
                    f"HTTP {response.status_code}",

                "details":
                    data

            }), response.status_code


        task_id = data.get(
            "task_id"
        )


        if not task_id:

            return jsonify({

                "error":
                    "MiniMax returned no task_id.",

                "details":
                    data

            }), 502


        return jsonify({

            "task_id":
                task_id

        })


    except Exception as e:

        return jsonify({

            "error":
                str(e)

        }), 500


@app.get("/status/<task_id>")
def status(task_id):

    try:

        response = requests.get(

            f"{MINIMAX_BASE_URL}"
            f"/v2/query/video_generation/{task_id}",

            headers={

                "Authorization":
                    f"Bearer {MINIMAX_API_KEY}"

            },

            timeout=60

        )


        try:

            data = response.json()

        except Exception:

            data = {
                "raw":
                    response.text
            }


        if response.status_code >= 400:

            return jsonify({

                "error":
                    f"MiniMax status API error "
                    f"HTTP {response.status_code}",

                "details":
                    data

            }), response.status_code


        task = data.get("task") or {}

        task_status = task.get(
            "status"
        )


        result = {

            "status":
                task_status

        }


        if task_status == "succeeded":

            content = (
                task.get("content") or {}
            )


            video_url = content.get(
                "url"
            )


            if not video_url:

                return jsonify({

                    "error":
                        "MiniMax task succeeded "
                        "but returned no video URL.",

                    "details":
                        data

                }), 502


            result["video_url"] = video_url


        if task_status == "failed":

            result["error"] = (
                task.get("error") or {}
            )


        return jsonify(result)


    except Exception as e:

        return jsonify({

            "error":
                str(e)

        }), 500


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )


    app.run(

        host="0.0.0.0",

        port=port

    )
