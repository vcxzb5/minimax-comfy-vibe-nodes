"""Custom ComfyUI nodes for the vcxzb5 MiniMax workflow setup."""

from copy import deepcopy
import os

try:
    from videohelpersuite.nodes import VideoCombine
except ImportError as exc:  # pragma: no cover - exercised by ComfyUI loading
    raise ImportError(
        "MiniMax Comfy Vibe Nodes requires ComfyUI-VideoHelperSuite to be installed."
    ) from exc


class SingleFileVideoCombine(VideoCombine):
    """Video Helper Suite's Video Combine, retaining only the requested output.

    VideoHelperSuite normally writes a metadata PNG and, when audio is supplied,
    an intermediate silent video before producing the muxed video.  Its cleanup
    option removes the intermediate files after processing.  This variant also
    disables the metadata PNG and enables cleanup, leaving only the final video
    (audio-muxed when audio is connected).
    """

    CATEGORY = "Vibe Nodes/Video"

    def combine_video(self, *args, **kwargs):
        extra_pnginfo = kwargs.get("extra_pnginfo")
        if extra_pnginfo is None:
            extra_pnginfo = {}
        else:
            extra_pnginfo = deepcopy(extra_pnginfo)

        workflow = extra_pnginfo.setdefault("workflow", {})
        if not isinstance(workflow, dict):
            workflow = {}
            extra_pnginfo["workflow"] = workflow
        extra = workflow.setdefault("extra", {})
        if not isinstance(extra, dict):
            extra = {}
            workflow["extra"] = extra

        # These are consumed by VHS's VideoCombine implementation.
        extra["VHS_MetadataImage"] = False
        extra["VHS_KeepIntermediate"] = False
        kwargs["extra_pnginfo"] = extra_pnginfo

        result = super().combine_video(*args, **kwargs)

        # VHS includes the deliberately-disabled metadata path in its returned
        # filename list. Expose only files that actually exist to downstream UI.
        if isinstance(result, dict):
            result = dict(result)
            returned = result.get("result")
            if isinstance(returned, tuple) and len(returned) == 1:
                save_output, filenames = returned[0]
                if isinstance(filenames, list):
                    result["result"] = ((
                        save_output,
                        [path for path in filenames if os.path.exists(path)],
                    ),)
        return result


NODE_CLASS_MAPPINGS = {
    "VibeSingleFileVideoCombine": SingleFileVideoCombine,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VibeSingleFileVideoCombine": "Video Combine (Single File)",
}
