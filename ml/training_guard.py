"""
A safety wrapper around training runs — NOT a hardware-protection
mechanism (a training script crashing cannot damage a GPU; that's
handled by the GPU's own firmware regardless of what Python does).

What this actually protects against:
1. Losing all training progress when a GPU error occurs mid-run.
2. Leaving GPU memory in a stuck state after a crash, blocking the
   next attempt or another process on a shared machine.
3. Silent or confusing failures — every failure is logged with what
   happened and exits with a clear status, not a raw traceback.
"""

import logging

import torch

logger = logging.getLogger("ml.training_guard")

GPU_ERROR_MARKERS = ("CUDA", "out of memory", "cudnn", "cuDNN", "device-side assert")


def _looks_like_gpu_error(exc: Exception) -> bool:
    return any(marker.lower() in str(exc).lower() for marker in GPU_ERROR_MARKERS)


def _cleanup_gpu_memory():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        logger.info("GPU memory cache cleared")


def safe_train(
    train_step_fn,
    num_epochs: int,
    val_step_fn=None,
    patience: int = 15,
    checkpoint_fn=None,
    checkpoint_every: int = 50,
    model_name: str = "model",
) -> dict:
    last_loss = None
    best_val_loss = float("inf")
    epochs_without_improvement = 0

    for epoch in range(num_epochs):
        try:
            last_loss = train_step_fn(epoch)

            if val_step_fn is not None:
                val_loss = val_step_fn(epoch)
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    epochs_without_improvement = 0
                    if checkpoint_fn is not None:
                        checkpoint_fn()
                        logger.info(
                            f"[{model_name}] best checkpoint saved at epoch {epoch + 1} (val_loss: {val_loss:.5f})"
                        )
                else:
                    epochs_without_improvement += 1

                if epochs_without_improvement >= patience:
                    logger.info(
                        f"[{model_name}] early stopping triggered at epoch {epoch + 1}"
                    )
                    return {
                        "status": "completed",
                        "last_epoch": epoch,
                        "last_loss": last_loss,
                        "best_val_loss": best_val_loss,
                        "error": None,
                    }
            else:
                if checkpoint_fn is not None and (epoch + 1) % checkpoint_every == 0:
                    checkpoint_fn()
                    logger.info(f"[{model_name}] checkpoint saved at epoch {epoch + 1}")

        except Exception as exc:
            is_gpu_error = _looks_like_gpu_error(exc)
            logger.error(
                f"[{model_name}] training failed at epoch {epoch + 1}/{num_epochs} "
                f"({'GPU-related' if is_gpu_error else 'non-GPU'} error): {exc}"
            )

            if checkpoint_fn is not None:
                try:
                    checkpoint_fn()
                    logger.info(
                        f"[{model_name}] emergency checkpoint saved at epoch {epoch}"
                    )
                except Exception as checkpoint_exc:
                    logger.error(
                        f"[{model_name}] emergency checkpoint ALSO failed: {checkpoint_exc}"
                    )

            if is_gpu_error:
                _cleanup_gpu_memory()
                if "out of memory" in str(exc).lower():
                    logger.error(
                        f"[{model_name}] this looks like a CUDA out-of-memory error — "
                        f"reduce batch size or model size and retry, rather than assuming "
                        f"the GPU hardware is at fault."
                    )

            return {
                "status": "failed",
                "last_epoch": epoch,
                "last_loss": last_loss,
                "error": str(exc),
            }

    return {
        "status": "completed",
        "last_epoch": num_epochs - 1,
        "last_loss": last_loss,
        "error": None,
    }
