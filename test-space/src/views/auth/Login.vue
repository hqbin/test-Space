<template>
  <div
    class="min-h-screen flex items-center justify-center p-8"
    style="background: radial-gradient(circle at 50% 0%, #DAE1FF 0%, #F9F9FB 50%)"
  >
    <div class="glass-panel rounded-[2rem] p-12 w-full max-w-[420px] shadow-sm">
      <div class="text-center mb-10">
        <h1 class="font-display-lg text-display-lg font-black text-on-surface tracking-tighter">Test Space</h1>
        <p class="font-body-lg text-body-lg text-on-surface-variant mt-2">Sign in to your workspace</p>
      </div>

      <form @submit.prevent="handleLogin" class="flex flex-col gap-6">
        <!-- Captcha -->
        <div class="flex justify-center mb-2">
          <img
            v-if="captchaImage"
            :src="captchaImage"
            @click="loadCaptcha"
            class="rounded-xl cursor-pointer h-16 border border-glass-border-light"
            title="Click to refresh"
          />
          <div v-else class="h-16 w-40 rounded-xl bg-surface-container-low animate-pulse"></div>
        </div>

        <!-- Username -->
        <div>
          <label class="block font-label-md text-caption text-on-surface uppercase tracking-wider mb-2">Username</label>
          <input
            v-model="username"
            class="w-full bg-white border border-outline-variant rounded-lg px-4 py-3 text-body-md text-on-surface focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all shadow-sm recessed-input"
            type="text"
            placeholder="Enter your username"
            required
          />
        </div>

        <!-- Password -->
        <div>
          <label class="block font-label-md text-caption text-on-surface uppercase tracking-wider mb-2">Password</label>
          <input
            v-model="password"
            class="w-full bg-white border border-outline-variant rounded-lg px-4 py-3 text-body-md text-on-surface focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all shadow-sm recessed-input"
            type="password"
            placeholder="Enter your password"
            required
          />
        </div>

        <!-- Captcha Code -->
        <div>
          <label class="block font-label-md text-caption text-on-surface uppercase tracking-wider mb-2">Verification Code</label>
          <input
            v-model="captchaCode"
            class="w-full bg-white border border-outline-variant rounded-lg px-4 py-3 text-body-md text-on-surface focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all shadow-sm recessed-input"
            type="text"
            placeholder="Enter code from image"
            required
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full glass-button font-label-md text-label-md py-3 rounded-full transition-all disabled:opacity-50 shadow-sm"
        >
          {{ loading ? "Signing in..." : "Sign In" }}
        </button>

        <p v-if="error" class="text-error text-center font-label-md text-label-md">{{ error }}</p>
      </form>
      <div class="mt-6 pt-6 border-t border-glass-border-light/50 text-center">
        <button
          class="glass-button font-caption text-caption"
          @click="skipLogin"
        >
          Enter Workspace (Dev Mode)
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "@/stores/user";
import { getCaptcha } from "@/api/captcha";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

  function skipLogin() {
    const fakeUser = { username: "devuser", full_name: "Dev User", role: "admin", id: 1 };
    localStorage.setItem("token", "dev-token");
    localStorage.setItem("user", JSON.stringify(fakeUser));
    userStore.token = "dev-token";
    userStore.userInfo = fakeUser as any;
    const redirect = (route.query.redirect as string) || "/workspace";
    router.push(redirect);
  }

  const username = ref("");
  const password = ref("");
  const captchaCode = ref("");
const captchaId = ref("");
const captchaImage = ref("");
const loading = ref(false);
const error = ref("");

async function loadCaptcha() {
  try {
    const res: any = await getCaptcha();
    if (res.data) {
      captchaId.value = res.data.captcha_id;
      captchaImage.value = res.data.captcha_image;
    }
  } catch {
    error.value = "Failed to load captcha";
  }
}

async function handleLogin() {
  if (!username.value || !password.value || !captchaCode.value) return;
  loading.value = true;
  error.value = "";
  try {
    await userStore.login({
      username: username.value,
      password: password.value,
      captcha_id: captchaId.value,
      captcha_code: captchaCode.value,
    });
    const redirect = (route.query.redirect as string) || "/workspace";
    router.push(redirect);
  } catch (err: any) {
    error.value = err.message || "Login failed";
    loadCaptcha();
    captchaCode.value = "";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadCaptcha();
});
</script>
