FROM tensorflow/tensorflow

WORKDIR /usr/src/backend-api

COPY . .

WORKDIR /usr/src/backend-api/saved_model/ml-aksacarma/variables

RUN apt update && apt install wget -y && \ 
    wget https://storage.googleapis.com/variables-data-model/variables.data-00000-of-00001 -O variables.data-00000-of-00001 && \
    apt purge --autoremove wget -y && apt clean

WORKDIR /usr/src/backend-api

ARG SECRET_KEY \
    GOOGLE_KEY_1 \
    GOOGLE_KEY_2 \
    GOOGLE_KEY_3 \
    GOOGLE_KEY_4 \
    GOOGLE_KEY_5 \
    DB_HOST \
    DB_PORT \
    DB_USER \
    DB_PASS \
    DB_NAME \
    SA_KEY

ENV SECRET_KEY=${SECRET_KEY} \
    GOOGLE_KEY_1=${GOOGLE_KEY_1} \
    GOOGLE_KEY_2=${GOOGLE_KEY_2} \
    GOOGLE_KEY_3=${GOOGLE_KEY_3} \
    GOOGLE_KEY_4=${GOOGLE_KEY_4} \
    GOOGLE_KEY_5=${GOOGLE_KEY_5} \
    DB_HOST=${DB_HOST} \
    DB_PORT=${DB_PORT} \
    DB_USER=${DB_USER} \
    DB_PASS=${DB_PASS} \
    DB_NAME=${DB_NAME} \
    SA_KEY=${SA_KEY}
# ENV ZIP_PASS=${ZIP_PASS}
# ENV GOOGLE_APPLICATION_CREDENTIALS=./aksacarma-2e5f57e8e8c5.json

RUN [ "pip", "install", "-r", "requirements.txt" ]
# RUN [ "wget", "https://cdn.jeyy.xyz/application/aksacarma_cloud_storage_sa_a850f4.zip" ]
# RUN [ "7z", "x", "aksacarma_cloud_storage_sa_a850f4.zip", "-p${ZIP_PASS}" ]

# ENV CUDA_VISIBLE_DEVICES='-1'

# CMD [ "python", "-m", "uvicorn", "main:app", "--port", "8005", "--host", "0.0.0.0"]
CMD [ "python", "main.py" ]
