FROM vllm/vllm-openai:v0.28.0

CMD ["--model", "Qwen/Qwen2.5-0.5B-Instruct", "--host", "0.0.0.0", "--port", "8000", "--dtype", "half", "--gpu-memory-utilization", "0.80", "--max-model-len", "2048"]
