import { app } from "../../../scripts/app.js";

const NODE_NAME = "VibeLoadVideoUploadNoAudioCrash";

app.registerExtension({
    name: "vcxzb5.minimax-comfy-directory-video",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData?.name !== NODE_NAME) return;

        const originalCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function (...args) {
            const result = originalCreated?.apply(this, args);
            const directoryWidget = this.widgets?.find((w) => w.name === "directory");
            const videoWidget = this.widgets?.find((w) => w.name === "video");
            if (!directoryWidget || !videoWidget || this.__directoryVideoReady) {
                return result;
            }
            this.__directoryVideoReady = true;

            const allVideos = [...(videoWidget.options?.values || [])];
            const updateVideos = () => {
                const directory = directoryWidget.value || "";
                const prefix = directory ? `${directory.replace(/\/$/, "")}/` : "";
                const values = allVideos.filter((path) => {
                    if (!prefix) return !path.includes("/");
                    return path.startsWith(prefix);
                });
                videoWidget.options.values = values;
                if (!values.includes(videoWidget.value)) {
                    videoWidget.value = values[0] || "";
                    videoWidget.callback?.(videoWidget.value);
                }
                this.setDirtyCanvas?.(true, true);
            };

            const originalDirectoryCallback = directoryWidget.callback;
            directoryWidget.callback = (value, ...callbackArgs) => {
                const result = originalDirectoryCallback?.call(
                    directoryWidget, value, ...callbackArgs
                );
                updateVideos();
                return result;
            };
            updateVideos();
            return result;
        };
    },
});
