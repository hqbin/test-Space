<template>
  <div class="w-screen h-screen bg-black flex flex-col overflow-hidden select-none">
    <!-- Mirror canvas area -->
    <div class="flex-1 min-h-0 relative">
      <canvas ref="mirrorCanvas" class="w-full h-full object-contain block"
        @mousedown="onPointerDown"
        @mouseup="onPointerUp"
        @touchstart.prevent="onPointerDown($event.touches[0])"
        @touchend.prevent="onPointerUp($event.changedTouches[0])"
        @contextmenu.prevent="onRightClick"></canvas>
    </div>

    <!-- Remote Control Bar -->
    <div class="bg-[#1a1c1d] border-t border-white/10 flex-shrink-0 px-2 py-2">
      <!-- Row 1: System buttons + D-pad -->
      <div class="flex items-center justify-center gap-3 mb-2">
        <!-- Left: Back, Home, Settings -->
        <div class="flex gap-1">
          <button class="remote-btn" @click="sendKey('4')">
            <span class="material-symbols-outlined text-lg">arrow_back</span>
          </button>
          <button class="remote-btn" @click="sendKey('3')">
            <span class="material-symbols-outlined text-lg">home</span>
          </button>
          <button class="remote-btn" @click="sendKey('176')">
            <span class="material-symbols-outlined text-lg">settings</span>
          </button>
        </div>
        <!-- Center: D-pad -->
        <div class="relative w-[108px] h-[108px] flex-none">
          <div class="absolute top-0 left-1/2 -translate-x-1/2">
            <button class="dpad-btn" @click="sendKey('19')">
              <span class="material-symbols-outlined text-base">keyboard_arrow_up</span>
            </button>
          </div>
          <div class="absolute bottom-0 left-1/2 -translate-x-1/2">
            <button class="dpad-btn" @click="sendKey('20')">
              <span class="material-symbols-outlined text-base">keyboard_arrow_down</span>
            </button>
          </div>
          <div class="absolute left-0 top-1/2 -translate-y-1/2">
            <button class="dpad-btn" @click="sendKey('21')">
              <span class="material-symbols-outlined text-base">keyboard_arrow_left</span>
            </button>
          </div>
          <div class="absolute right-0 top-1/2 -translate-y-1/2">
            <button class="dpad-btn" @click="sendKey('22')">
              <span class="material-symbols-outlined text-base">keyboard_arrow_right</span>
            </button>
          </div>
          <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
            <button class="dpad-btn w-8 h-8 bg-white/10 rounded-full flex items-center justify-center" @click="sendKey('23')">
              <span class="material-symbols-outlined text-base text-white/90">check</span>
            </button>
          </div>
        </div>
        <!-- Right: Power + Volume -->
        <div class="flex gap-1">
          <button class="remote-btn !bg-red-500/20 !text-red-400" @click="sendKey('26')">
            <span class="material-symbols-outlined text-lg">power_settings_new</span>
          </button>
          <button class="remote-btn" @click="sendKey('24')">
            <span class="material-symbols-outlined text-lg">volume_up</span>
          </button>
          <button class="remote-btn" @click="sendKey('25')">
            <span class="material-symbols-outlined text-lg">volume_down</span>
          </button>
          <button class="remote-btn" @click="sendKey('164')">
            <span class="material-symbols-outlined text-lg">volume_off</span>
          </button>
        </div>
      </div>
      <!-- Row 2: Numpad 0-9 -->
      <div class="flex items-center justify-center gap-1">
        <button v-for="n in 9" :key="n" class="numpad-btn" @click="sendKey(String(7 + n))">{{ n }}</button>
        <button class="numpad-btn" @click="sendKey('0')">0</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { listen } from "@tauri-apps/api/event";
import { invoke, Channel } from "@tauri-apps/api/core";
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";

const appWindow = getCurrentWebviewWindow();
const listenTarget = { target: { kind: 'WebviewWindow' as const, label: appWindow.label } };

const serial = new URLSearchParams(window.location.search).get("serial") || "";
const quality = new URLSearchParams(window.location.search).get("quality") || "smooth";
const qualityMode = quality === 'quality' ? 'quality' : 'smooth';
const mirrorCanvas = ref<HTMLCanvasElement | null>(null);
let ctx: CanvasRenderingContext2D | null = null;
let unlisteners: (() => void)[] = [];
let videoDecoder: VideoDecoder | null = null;
let decoderConfigured = false;
let useScrcpy = false;
let tapX1 = 0, tapY1 = 0, tapping = false;
let mirrorW = 0, mirrorH = 0;
let devW = 0, devH = 0;


async function sendKey(keycode: string) {
  try { await invoke("adb_input_keyevent", { serial, keycode }); } catch {}
}

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
        error: () => { gotKeyFrame = false; },
      });
    }
  }, listenTarget));

  let gotKeyFrame = false;
  let decoderConfigured = false;

  const onFrame = new Channel<ArrayBuffer>();
  onFrame.onmessage = (raw: ArrayBuffer) => {
    if (!raw || raw.byteLength === 0) return;
    const bytes = new Uint8Array(raw);
    if (bytes[0] === 0xFF) {
      if (useScrcpy && videoDecoder && !decoderConfigured) {
        try {
          videoDecoder.configure({
            codec: "avc1.42E01E",
            description: bytes.subarray(1),
            codedWidth: 1280, codedHeight: 720,
          });
          decoderConfigured = true;
        } catch {}
      }
      return;
    }
    const isKey = bytes[0] === 1;
    const frameData = bytes.subarray(1);

    if (isKey) gotKeyFrame = true;
    if (!gotKeyFrame) return;

    if (useScrcpy && videoDecoder && decoderConfigured) {
      videoDecoder.decode(new EncodedVideoChunk({
        type: isKey ? "key" : "delta",
        timestamp: performance.now() * 1000,
        data: frameData,
      }));
    } else if (!useScrcpy) {
      const c = mirrorCanvas.value; if (!c || !ctx) return;
      const blob = new Blob([frameData], { type: "image/png" });
      const url = URL.createObjectURL(blob);
      const img = new window.Image();
      img.onload = () => {
        c.width = img.width; c.height = img.height;
        mirrorW = img.width; mirrorH = img.height;
        ctx!.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
      };
      img.onerror = () => URL.revokeObjectURL(url);
      img.src = url;
    }
  };

  unlisteners.push(await listen("mirror:ready", () => {}, listenTarget));

  await invoke("adb_mirror_start", {
    serial,
    onFrame,
    maxSize: qualityMode === 'quality' ? 1080 : 960,
    videoBitRate: qualityMode === 'quality' ? 5_000_000 : 3_000_000,
    maxFps: qualityMode === 'quality' ? 24 : 15,
  });
});

onUnmounted(() => {
  for (const u of unlisteners) u();
  unlisteners = [];
  invoke("adb_mirror_stop", { serial }).catch(() => {});
  if (videoDecoder) { videoDecoder.close(); videoDecoder = null; }
});
</script>

<style scoped>
.remote-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}
.remote-btn:hover {
  background: rgba(255, 255, 255, 0.18);
  transform: scale(1.08);
}
.remote-btn:active {
  transform: scale(0.95);
  background: rgba(255, 255, 255, 0.25);
}

.dpad-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}
.dpad-btn:hover {
  background: rgba(255, 255, 255, 0.18);
  transform: scale(1.12);
}
.dpad-btn:active {
  transform: scale(0.92);
}

.numpad-btn {
  width: 30px;
  height: 26px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 11px;
  font-family: monospace;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}
.numpad-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  color: rgba(255, 255, 255, 0.95);
  transform: scale(1.08);
}
.numpad-btn:active {
  transform: scale(0.95);
}
</style>
