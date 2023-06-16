import tensorflow as tf
import numpy as np
from io import BytesIO
from PIL import Image

new_model = tf.keras.models.load_model("./saved_model/ml-aksacarma")

skin_type_desease = [
    "Acne and rosacea",
    "Bullous disease",
    "Eczema",
    "Melanoma skin cancer nevi and moles",
    "Scabies lyme disease and other infestations and bites",
    "Tinea ringworm candidiasis and other fungal infections",
    "Urticaria hives",
    "Vascular tumors",
    "Vasculitis",
    "Warts molluscum and other viral infections",
]


def what_class(class_prediction):
    index_prediction = np.argmax(class_prediction)
    probability_prediction = class_prediction[index_prediction]

    if probability_prediction < 0.5:
        return None

    return skin_type_desease[index_prediction]


def detect_skin_image(image: bytes):
    buf = BytesIO(image)
    image = Image.open(buf).resize((150, 150)).convert("RGB")
    npa = np.array(image)
    npa = np.expand_dims(npa, axis=0)
    npa = npa / 255.0

    prediction = new_model.predict(npa)[0]

    return what_class(prediction)
