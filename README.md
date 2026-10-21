# MiniMax Comfy Vibe Nodes

Custom ComfyUI nodes for the `vcxzb5` MiniMax workflows.

## Installation

Install this repository in ComfyUI's `custom_nodes` directory alongside
[ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite):

```bash
git clone https://github.com/vcxzb5/minimax-comfy-vibe-nodes.git \
  /workspace/ComfyUI/custom_nodes/minimax-comfy-vibe-nodes
```

Restart ComfyUI after installation.

## Nodes

### Video Combine (Single File)

A wrapper around VideoHelperSuite's `Video Combine` node. It suppresses the
metadata image and removes the silent intermediate video, leaving exactly one
output file:

- with audio: the video containing audio;
- without audio: the video without audio.

VideoHelperSuite remains a runtime dependency because this node reuses its
format handling and encoding implementation.

### Load Video (Upload) (No Audio Crash)

A modified VideoHelperSuite upload loader that probes the uploaded container
for an audio stream before exposing the lazy audio output. Silent videos return
`None` for audio instead of failing later when VideoHelperSuite tries to run
FFmpeg with no audio stream.

### MiniMax Aspect Resize

Accepts an IMAGE batch and resizes it while preserving its aspect ratio. The
result fits inside an oriented `720 x 1088` bounding box, with dimensions
rounded down to multiples of 16 for model compatibility. It outputs the resized
image batch plus its width and height as integer values. Landscape video is
bounded by `1088 x 720`, while portrait video is bounded by `720 x 1088`.
The `multiplier` input scales that target size before alignment rounding: `1.0`
keeps the default behavior, while `0.7` requests approximately 70% resolution.
