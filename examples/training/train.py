import torch
from torch import nn


def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required for this training workload")

    device = torch.device("cuda")

    print(f"torch_version={torch.__version__}")
    print(f"cuda_available={torch.cuda.is_available()}")
    print(f"cuda_device={torch.cuda.get_device_name(0)}")

    torch.manual_seed(42)

    features = torch.randn(4096, 128, device=device)
    targets = torch.randint(
        0,
        10,
        (4096,),
        device=device,
    )

    model = nn.Sequential(
        nn.Linear(128, 256),
        nn.ReLU(),
        nn.Linear(256, 10),
    ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=1e-3,
    )
    criterion = nn.CrossEntropyLoss()

    model.train()

    for epoch in range(1, 11):
        optimizer.zero_grad(set_to_none=True)

        logits = model(features)
        loss = criterion(logits, targets)

        loss.backward()
        optimizer.step()

        print(
            f"epoch={epoch} "
            f"loss={loss.item():.6f}"
        )

    print("TRAINING_COMPLETED")


if __name__ == "__main__":
    main()
