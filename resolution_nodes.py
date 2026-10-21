"""Resolution helpers for MiniMax video editing workflows."""

import torch
import torch.nn.functional as F


DEFAULT_SHORT_SIDE = 720
DEFAULT_LONG_SIDE = 1088
DEFAULT_ALIGNMENT = 16


def fit_dimensions(width, height, short_side=DEFAULT_SHORT_SIDE,
                   long_side=DEFAULT_LONG_SIDE, alignment=DEFAULT_ALIGNMENT,
                   multiplier=1.0):
    """Return aligned dimensions preserving the input aspect ratio.

    The result fits within an oriented bounding box of ``short_side`` by
    ``long_side``. Dimensions are rounded down to the requested alignment so
    they remain valid for common video models.
    """
    if width <= 0 or height <= 0:
        raise ValueError("Input dimensions must be positive")
    if short_side <= 0 or long_side <= 0 or alignment <= 0 or multiplier <= 0:
        raise ValueError("Target dimensions, alignment, and multiplier must be positive")

    short_side *= multiplier
    long_side *= multiplier
    input_long = max(width, height)
    input_short = min(width, height)
    scale = min(long_side / input_long, short_side / input_short)

    scaled_width = max(alignment, int(width * scale) // alignment * alignment)
    scaled_height = max(alignment, int(height * scale) // alignment * alignment)

    # Guard against a one-alignment rounding edge case.
    while scaled_width > long_side or scaled_height > long_side:
        if scaled_width >= scaled_height:
            scaled_width -= alignment
        else:
            scaled_height -= alignment
    return scaled_width, scaled_height


class MiniMaxAspectResize:
    """Resize an image batch to a MiniMax-friendly bounded resolution."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "multiplier": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.1,
                    "max": 1.0,
                    "step": 0.01,
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("images", "width", "height")
    FUNCTION = "resize"
    CATEGORY = "Vibe Nodes/Resolution"

    def resize(self, images, multiplier=1.0):
        if not isinstance(images, torch.Tensor) or images.ndim != 4:
            raise ValueError("images must be a ComfyUI IMAGE batch [B,H,W,C]")
        if images.shape[0] == 0:
            raise ValueError("images must contain at least one frame")

        height, width = images.shape[1:3]
        target_width, target_height = fit_dimensions(
            width, height, multiplier=multiplier
        )
        if (target_width, target_height) == (width, height):
            resized = images
        else:
            # ComfyUI IMAGE tensors are BHWC; interpolate expects NCHW.
            nchw = images.permute(0, 3, 1, 2)
            resized = F.interpolate(
                nchw,
                size=(target_height, target_width),
                mode="bilinear",
                align_corners=False,
                antialias=True,
            ).permute(0, 2, 3, 1).contiguous()

        return resized, target_width, target_height


NODE_CLASS_MAPPINGS = {
    "MiniMaxAspectResize": MiniMaxAspectResize,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxAspectResize": "MiniMax Aspect Resize",
}
