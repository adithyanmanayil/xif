from flask import Flask, render_template, request, send_file
from PIL import Image
import struct, json, os

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Save XIF (image + text layers)
def save_xif(image_path, text_layers, xif_path):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    pixels = img.tobytes()
    layers_json = json.dumps(text_layers).encode("utf-8")
    layers_len = len(layers_json)

    with open(xif_path, "wb") as f:
        f.write(b"XIF")
        f.write(bytes([1]))  # version
        f.write(struct.pack(">I", width))
        f.write(struct.pack(">I", height))
        f.write(struct.pack(">I", layers_len))
        f.write(layers_json)
        f.write(pixels)

# Load XIF
def load_xif(xif_path):
    with open(xif_path, "rb") as f:
        if f.read(3) != b"XIF":
            raise ValueError("Not a XIF file")
        version = f.read(1)[0]
        width = struct.unpack(">I", f.read(4))[0]
        height = struct.unpack(">I", f.read(4))[0]
        layers_len = struct.unpack(">I", f.read(4))[0]
        layers_json = f.read(layers_len)
        text_layers = json.loads(layers_json)
        img_data = f.read()
        img = Image.frombytes("RGB", (width, height), img_data)
        img_path = os.path.join(UPLOAD_FOLDER, "decoded.png")
        img.save(img_path)
        return img_path, text_layers

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/create_xif", methods=["POST"])
def create_xif():
    image_file = request.files["image"]
    layers = request.form.get("layers")  # JSON string
    text_layers = json.loads(layers)
    img_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
    image_file.save(img_path)
    xif_path = os.path.join(UPLOAD_FOLDER, "output.xif")
    save_xif(img_path, text_layers, xif_path)
    return send_file(xif_path, as_attachment=True)

@app.route("/decode", methods=["POST"])
def decode():
    xif_file = request.files["xif_file"]
    xif_path = os.path.join(UPLOAD_FOLDER, xif_file.filename)
    xif_file.save(xif_path)
    img_path, text_layers = load_xif(xif_path)
    return render_template("result.html", image_path=img_path, text_layers=text_layers)

if __name__ == "__main__":
    app.run(debug=True)
