from flask import Flask, request, jsonify
from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation
from PIL import Image
import torch
import numpy as np
import io
import base64

app = Flask(__name__)

# Load CLIPSeg processor and model
processor = CLIPSegProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
model = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined")

# Function to process image and generate mask
def process_image(image, prompt):
    inputs = processor(
        text=prompt, images=image, padding="max_length", return_tensors="pt"
    )
    with torch.no_grad():
        outputs = model(**inputs)
        preds = outputs.logits

    pred = torch.sigmoid(preds)
    mat = pred.cpu().numpy()
    mask = Image.fromarray(np.uint8(mat * 255), "L")
    mask = mask.convert("RGB")
    mask = mask.resize(image.size)
    mask = np.array(mask)[:, :, 0]

    mask_min = mask.min()
    mask_max = mask.max()
    mask = (mask - mask_min) / (mask_max - mask_min)

    return mask

# Function to get masks from positive or negative prompts
def get_masks(prompts, img, threshold):
    prompts = prompts.split(",")
    masks = []
    for prompt in prompts:
        mask = process_image(img, prompt)
        mask = mask > threshold
        masks.append(mask)

    return masks

# Route for processing requests
@app.route('/api', methods=['POST'])
def process_request():
    data = request.json

    # Convert base64 image to PIL Image
    base64_image = data.get('image')
    image_data = base64.b64decode(base64_image.split(',')[1])
    img = Image.open(io.BytesIO(image_data))

    # Get other parameters
    pos_prompts = data.get('positive_prompts', '')
    neg_prompts = data.get('negative_prompts', '')
    threshold = float(data.get('threshold', 0.4))

    # Perform image segmentation without caching
    positive_masks = get_masks(pos_prompts, img, 0.5)
    negative_masks = get_masks(neg_prompts, img, 0.5)

    pos_mask = np.any(np.stack(positive_masks), axis=0)
    neg_mask = np.any(np.stack(negative_masks), axis=0)
    final_mask = pos_mask & ~neg_mask

    final_mask = Image.fromarray(final_mask.astype(np.uint8) * 255, "L")

    # Convert final mask to base64
    buffered = io.BytesIO()
    final_mask.save(buffered, format="PNG")
    final_mask_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return jsonify({'final_mask_base64': final_mask_base64})
