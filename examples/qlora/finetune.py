from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
OUTPUT_DIR = Path("/artifacts/qlora-adapter")


def build_dataset(tokenizer):
    samples = [
        {
            "instruction": "Explain what a GPU scheduler does.",
            "response": (
                "A GPU scheduler selects an appropriate GPU resource "
                "for a workload based on placement constraints and capacity."
            ),
        },
        {
            "instruction": "Why is GPU memory important for AI workloads?",
            "response": (
                "GPU memory determines whether model parameters, activations, "
                "and training state can fit on the accelerator."
            ),
        },
        {
            "instruction": "What is QLoRA?",
            "response": (
                "QLoRA fine-tunes low-rank adapters while the base model "
                "is loaded using low-bit quantization."
            ),
        },
        {
            "instruction": "What does workload reconciliation mean?",
            "response": (
                "Workload reconciliation compares runtime state with control-plane "
                "state and updates lifecycle status when execution changes."
            ),
        },
    ]

    texts = []

    for sample in samples:
        messages = [
            {
                "role": "user",
                "content": sample["instruction"],
            },
            {
                "role": "assistant",
                "content": sample["response"],
            },
        ]

        texts.append(
            tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
        )

    return texts


def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required for QLoRA fine-tuning")

    print(f"torch_version={torch.__version__}")
    print(f"cuda_available={torch.cuda.is_available()}")
    print(f"cuda_device={torch.cuda.get_device_name(0)}")
    print(f"base_model={MODEL_ID}")
    print("quantization=4bit")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=quantization_config,
        device_map={"": 0},
    )

    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
        ],
    )

    model = get_peft_model(
        model,
        lora_config,
    )

    trainable, total = model.get_nb_trainable_parameters()

    print(f"trainable_parameters={trainable}")
    print(f"total_parameters={total}")
    print(
        f"trainable_percent="
        f"{100 * trainable / total:.4f}"
    )

    texts = build_dataset(tokenizer)

    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt",
    )

    input_ids = encoded["input_ids"].to("cuda")
    attention_mask = encoded["attention_mask"].to("cuda")

    labels = input_ids.clone()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=2e-4,
    )

    model.train()

    for step in range(1, 6):
        optimizer.zero_grad(set_to_none=True)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )

        loss = outputs.loss
        loss.backward()
        optimizer.step()

        print(
            f"step={step} "
            f"loss={loss.item():.6f}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print(f"adapter_saved={OUTPUT_DIR}")
    print("QLORA_TRAINING_COMPLETED")


if __name__ == "__main__":
    main()
