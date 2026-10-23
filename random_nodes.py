"""Small random-selection nodes for prompt and workflow utilities."""

import random


class RandomStringPicker:
    """Choose one of one to ten supplied strings at random."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "string_1": ("STRING", {"default": ""}),
            },
            "optional": {
                f"string_{index}": ("STRING",)
                for index in range(2, 11)
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "pick"
    CATEGORY = "Vibe Nodes/Utilities"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Ensure the node re-runs on every queue so a new random choice can be
        # made even when the upstream inputs have not changed.
        return float("nan")

    def pick(self, string_1, **kwargs):
        values = [string_1]
        values.extend(kwargs.get(f"string_{index}") for index in range(2, 11))
        # Treat empty and whitespace-only inputs as unprovided options.
        values = [value for value in values if value is not None and str(value).strip()]
        if not values:
            raise ValueError("Random String Picker needs at least one non-blank string")
        return (random.choice(values),)


NODE_CLASS_MAPPINGS = {
    "VibeRandomStringPicker": RandomStringPicker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VibeRandomStringPicker": "Random String Picker (1-10)",
}
