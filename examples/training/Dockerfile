FROM pytorch/pytorch:2.11.0-cuda12.8-cudnn9-runtime

WORKDIR /workload

COPY train.py /workload/train.py

CMD ["python", "/workload/train.py"]
