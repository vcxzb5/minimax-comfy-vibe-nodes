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
