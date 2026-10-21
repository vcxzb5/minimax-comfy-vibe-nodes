"""Custom ComfyUI nodes for the vcxzb5 MiniMax workflow setup."""

from copy import deepcopy
import os
import shutil
import subprocess
import sys

import folder_paths

# ComfyUI loads each custom-node directory independently. Add the sibling
# VideoHelperSuite package to sys.path without modifying the upstream install.
_vhs_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "comfyui-videohelpersuite")
)
if os.path.isdir(os.path.join(_vhs_root, "videohelpersuite")):
    sys.path.insert(0, _vhs_root)

from videohelpersuite.utils import ffmpeg_path, strip_path
from .resolution_nodes import MiniMaxAspectResize

try:
    from videohelpersuite.nodes import VideoCombine
    from videohelpersuite.load_video_nodes import LoadVideoUpload
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


class LoadVideoUploadNoAudioCrash(LoadVideoUpload):
    """VideoHelperSuite upload loader that treats silent videos as audio-less.

    VideoHelperSuite lazily extracts audio, but its extractor raises when a
    video has no audio stream. ComfyUI still needs a valid optional AUDIO value,
    so this node probes the container first and returns ``None`` for silent
    videos instead of a lazy extractor that will fail later during caching.
    """

    CATEGORY = "Vibe Nodes/Video"

    @classmethod
    def INPUT_TYPES(cls):
        inputs = super().INPUT_TYPES()
        input_dir = folder_paths.get_input_directory()
        videos = []
        directories = {""}
        for root, _, filenames in os.walk(input_dir):
            relative_dir = os.path.relpath(root, input_dir)
            if relative_dir == ".":
                relative_dir = ""
            else:
                directories.add(relative_dir.replace(os.sep, "/"))
            for filename in filenames:
                if os.path.splitext(filename)[1].lower() not in (".webm", ".mp4", ".mkv", ".gif", ".mov"):
                    continue
                relative = os.path.relpath(os.path.join(root, filename), input_dir)
                videos.append(relative.replace(os.sep, "/"))
        inputs["required"]["directory"] = (sorted(directories),)
        inputs["required"]["video"] = (sorted(videos),)
        return inputs

    @staticmethod
    def _has_audio_stream(path):
        ffprobe = shutil.which("ffprobe")
        if ffprobe is None and ffmpeg_path:
            ffprobe = os.path.join(os.path.dirname(ffmpeg_path), "ffprobe")
        if not ffprobe or not os.path.exists(ffprobe):
            # Preserve VideoHelperSuite's normal behavior if probing is
            # unavailable; this avoids silently dropping valid audio.
            return None

        probe = subprocess.run(
            [
                ffprobe,
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=index",
                "-of", "csv=p=0",
                path,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode != 0:
            return None
        return bool(probe.stdout.strip())

    def load_video(self, **kwargs):
        # The directory is a UI selector; the selected video already contains
        # its input-relative path and VHS resolves it safely.
        kwargs.pop("directory", None)
        video_path = folder_paths.get_annotated_filepath(
            strip_path(kwargs["video"])
        )
        result = super().load_video(**kwargs)
        has_audio = self._has_audio_stream(video_path)
        if has_audio is False:
            result = (*result[:2], None, result[3])
        return result


NODE_CLASS_MAPPINGS = {
    "VibeSingleFileVideoCombine": SingleFileVideoCombine,
    "VibeLoadVideoUploadNoAudioCrash": LoadVideoUploadNoAudioCrash,
    "MiniMaxAspectResize": MiniMaxAspectResize,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VibeSingleFileVideoCombine": "Video Combine (Single File)",
    "VibeLoadVideoUploadNoAudioCrash": "Load Video (Upload) (No Audio Crash)",
    "MiniMaxAspectResize": "MiniMax Aspect Resize",
}
