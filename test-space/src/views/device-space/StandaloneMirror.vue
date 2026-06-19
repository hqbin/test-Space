<template>
  <div class="w-screen h-screen bg-black overflow-hidden">
    <canvas ref="mirrorCanvas" class="w-full h-full object-contain block"
      @mousedown="onPointerDown"
      @mouseup="onPointerUp"
      @touchstart.prevent="onPointerDown($event.touches[0])"
      @touchend.prevent="onPointerUp($event.changedTouches[0])"
      @contextmenu.prevent="onRightClick"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { listen } from "@tauri-apps/api/event";
import { invoke } from "@tauri-apps/api/core";

const serial = new URLSearchParams(window.location.search).get("serial") || "";
const mirrorCanvas = ref<HTMLCanvasElement | null>(null);
let ctx: CanvasRenderingContext2D | null = null;
let unlisteners: (() => void)[] = [];
let videoDecoder: VideoDecoder | null = null;
let decoderConfigured = false;
let useScrcpy = false;
let tapX1 = 0, tapY1 = 0, tapping = false;
let mirrorW = 0, mirrorH = 0;
let devW = 0, devH = 0;

function canvasCoords(e: { clientX: number; clientY: number }) {
  const c = mirrorCanvas.value;
  if (!c || !mirrorW || !devW) return null;
  const r = c.getBoundingClientRect();
  const imgA = mirrorW / mirrorH;
  const conA = r.width / r.height;
  let dW: number, dH: number, oX: number, oY: number;
  if (imgA > conA) { dW = r.width; dH = r.width / imgA; oX = 0; oY = (r.height - dH) / 2; }
  else { dH = r.height; dW = r.height * imgA; oX = (r.width - dW) / 2; oY = 0; }
  const ix = e.clientX - r.left - oX;
  const iy = e.clientY - r.top - oY;
  if (ix < 0 || ix > dW || iy < 0 || iy > dH) return null;
  const vx = Math.round(ix * (mirrorW / dW));
  const vy = Math.round(iy * (mirrorH / dH));
  return { x: Math.round(vx * (devW / mirrorW)), y: Math.round(vy * (devH / mirrorH)) };
}

async function onPointerDown(e: MouseEvent | Touch) {
  const c = canvasCoords(e); if (!c) return;
  tapX1 = c.x; tapY1 = c.y; tapping = true;
  await invoke("adb_input_tap", { serial, x: c.x, y: c.y });
}

async function onPointerUp(e: MouseEvent | Touch) {
  if (!tapping) return; tapping = false;
  const c = canvasCoords(e); if (!c) return;
  if (Math.abs(c.x - tapX1) > 10 || Math.abs(c.y - tapY1) > 10) {
    await invoke("adb_input_swipe", { serial, x1: tapX1, y1: tapY1, x2: c.x, y2: c.y, duration: 200 });
  }
}

async function onRightClick() {
  await invoke("adb_input_keyevent", { serial, keycode: "BACK" });
}

onMounted(async () => {
  ctx = mirrorCanvas.value?.getContext("2d") || null;

  try {
    const [dw, dh] = await invoke<[number, number]>("adb_get_display_size", { serial });
    devW = dw; devH = dh;
  } catch {}

  unlisteners.push(await listen<string>("mirror:mode", (e) => {
    useScrcpy = e.payload === "scrcpy";
    if (useScrcpy) {
      videoDecoder = new VideoDecoder({
        output: (frame: VideoFrame) => {
          if (!ctx || !mirrorCanvas.value) { frame.close(); return; }
          mirrorCanvas.value.width = frame.displayWidth;
          mirrorCanvas.value.height = frame.displayHeight;
          mirrorW = frame.displayWidth; mirrorH = frame.displayHeight;
          ctx.drawImage(frame, 0, 0);
          frame.close();
        },
        error: () => {},
      });
    }
  }));

  unlisteners.push(await listen<string>("mirror:config", (e) => {
    if (!videoDecoder || decoderConfigured) return;
    try {
      videoDecoder.configure({
        codec: "avc1.42E01E",
        description: Uint8Array.from(atob(e.payload), c => c.charCodeAt(0)),
        codedWidth: 1280, codedHeight: 720,
      });
      decoderConfigured = true;
    } catch {}
  }));

  unlisteners.push(await listen<{ data: string; key: boolean; pts: number }>("mirror:frame", (e) => {
    if (!useScrcpy || !videoDecoder || !decoderConfigured) return;
    try {
      videoDecoder.decode(new EncodedVideoChunk({
        type: e.payload.key ? "key" : "delta",
        timestamp: e.payload.pts / 1000,
        data: Uint8Array.from(atob(e.payload.data), c => c.charCodeAt(0)),
      }));
    } catch {}
  }));

  unlisteners.push(await listen<string>("mirror:frame_data", (e) => {
    if (useScrcpy) return;
    const c = mirrorCanvas.value; if (!c || !ctx) return;
    const img = new window.Image();
    img.onload = () => {
      c.width = img.width; c.height = img.height;
      mirrorW = img.width; mirrorH = img.height;
      ctx!.drawImage(img, 0, 0);
    };
    img.src = `data:image/png;base64,${e.payload}`;
  }));

  unlisteners.push(await listen("mirror:ready", () => {}));

  await invoke("adb_mirror_start", { serial });
});

onUnmounted(() => {
  for (const u of unlisteners) u();
  unlisteners = [];
  invoke("adb_mirror_stop").catch(() => {});
  if (videoDecoder) { videoDecoder.close(); videoDecoder = null; }
});
</script>
