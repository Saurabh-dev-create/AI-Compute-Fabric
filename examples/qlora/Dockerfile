FROM pytorch/pytorch:2.11.0-cuda12.8-cudnn9-runtime

WORKDIR /workload

RUN pip install --no-cache-dir --break-system-packages \
    transformers==4.57.1 \
    peft==0.17.1 \
    accelerate==1.10.1 \
    bitsandbytes==0.47.0

COPY finetune.py /workload/finetune.py
COPY dataset.json /workload/dataset.json

RUN mkdir -p /artifacts/qlora-adapter

CMD ["python", "/workload/finetune.py"]
