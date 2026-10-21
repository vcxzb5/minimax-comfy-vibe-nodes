import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const LOAD_NODE = "VibeLoadVideoUploadNoAudioCrash";
const COMBINE_NODE = "VibeSingleFileVideoCombine";

function chain(object, property, callback) {
    const original = object[property];
    object[property] = function (...args) {
        const result = original?.apply(this, args);
        callback.apply(this, args);
        return result;
    };
}

function addVideoPreview(node) {
    const element = document.createElement("video");
    element.controls = true;
    element.loop = true;
    element.muted = true;
    element.style.width = "100%";
    element.style.maxHeight = "240px";
    element.style.objectFit = "contain";

    const widget = node.addDOMWidget("videopreview", "preview", element, {
        serialize: false,
        hideOnZoom: true,
        getValue: () => widget.value,
        setValue: (value) => { widget.value = value; },
    });
    widget.computeSize = (width) => [width, 180];
    widget.value = { params: {} };

    node.updateVideoPreview = (params) => {
        widget.value = { params: { ...(params || {}) } };
        const p = widget.value.params;
        if (!p.filename) {
            element.removeAttribute("src");
            element.load();
            return;
        }
        const url = api.apiURL("/view?" + new URLSearchParams({
            filename: p.filename,
            subfolder: p.subfolder || "",
            type: p.type || "input",
        }));
        element.src = url;
        element.load();
    };
}

function addUploadButton(node) {
    const pathWidget = node.widgets?.find((widget) => widget.name === "video");
    if (!pathWidget) return;

    const input = document.createElement("input");
    input.type = "file";
    input.accept = "video/webm,video/mp4,video/x-matroska,image/gif";
    input.style.display = "none";
    input.onchange = async () => {
        const file = input.files?.[0];
        if (!file) return;
        const body = new FormData();
        body.append("image", file, file.name);
        const response = await api.fetchApi("/upload/image", {
            method: "POST",
            body,
        });
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
        }
        const uploaded = await response.json();
        pathWidget.options.values ??= [];
        if (!pathWidget.options.values.includes(uploaded.name)) {
            pathWidget.options.values.push(uploaded.name);
        }
        pathWidget.value = uploaded.name;
        pathWidget.callback?.(uploaded.name);
        node.updateVideoPreview?.({
            filename: uploaded.name,
            type: "input",
            format: "video",
        });
    };
    node.onRemoved = ((original) => function () {
        input.remove();
        original?.apply(this, arguments);
    })(node.onRemoved);
    document.body.append(input);

    const button = node.addWidget("button", "choose video to upload", "", () => input.click());
    button.options.serialize = false;
}

app.registerExtension({
    name: "vcxzb5.minimax-comfy-vibe-previews",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData?.name === LOAD_NODE) {
            chain(nodeType.prototype, "onNodeCreated", function () {
                addUploadButton(this);
                addVideoPreview(this);
                const pathWidget = this.widgets?.find((widget) => widget.name === "video");
                pathWidget && chain(pathWidget, "callback", (value) => {
                    this.updateVideoPreview?.({
                        filename: value,
                        type: "input",
                        format: "video",
                    });
                });
                pathWidget?.callback?.(pathWidget.value);
            });
        } else if (nodeData?.name === COMBINE_NODE) {
            chain(nodeType.prototype, "onNodeCreated", function () {
                addVideoPreview(this);
            });
            chain(nodeType.prototype, "onExecuted", function (message) {
                if (message?.gifs?.[0]) {
                    this.updateVideoPreview?.(message.gifs[0]);
                }
            });
        }
    },
});
