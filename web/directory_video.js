import { app } from "../../../scripts/app.js";

const NODE_NAME = "VibeLoadVideoUploadNoAudioCrash";

function connectedSourceWidgets(node) {
    const input = node.inputs?.find((input) => input.name === "video");
    if (!input || !node.graph) return [];
    const linkIds = input.links || (input.link != null ? [input.link] : []);
    const widgets = [];
    for (const linkId of linkIds) {
        const link = node.graph.links?.[linkId];
        const source = link && node.graph.getNodeById?.(link.origin_id);
        const widget = source?.widgets?.find((widget) => widget.options?.values);
        if (widget) widgets.push(widget);
    }
    return widgets;
}

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
                const sourceWidgets = connectedSourceWidgets(this);
                for (const sourceWidget of sourceWidgets) {
                    sourceWidget.options.values = [...values];
                    if (!values.includes(sourceWidget.value)) {
                        sourceWidget.value = values[0] || "";
                        sourceWidget.callback?.(sourceWidget.value);
                    }
                }
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
            const originalConnectionsChange = this.onConnectionsChange;
            this.onConnectionsChange = function (...connectionArgs) {
                const connectionResult = originalConnectionsChange?.apply(this, connectionArgs);
                updateVideos();
                return connectionResult;
            };
            setTimeout(updateVideos, 0);
            return result;
        };
    },
});
