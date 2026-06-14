import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { login as loginApi } from "@/api/auth";
import type { LoginCredentials, UserInfo } from "@/types";

export const useUserStore = defineStore("user", () => {
  const userInfo = ref<UserInfo | null>(null);
  const token = ref(localStorage.getItem("token") || "");
  const avatarTimestamp = ref(Date.now());

  const loadUserFromStorage = () => {
    const stored = localStorage.getItem("user");
    if (stored) {
      try {
        userInfo.value = JSON.parse(stored);
      } catch {}
    }
  };

  const isLoggedIn = computed(() => !!token.value);

  const displayName = computed(() => {
    if (!userInfo.value) return "Guest";
    return userInfo.value.full_name || userInfo.value.username;
  });

  const avatarUrl = computed(() => {
    if (userInfo.value?.avatar) {
      if (userInfo.value.avatar.startsWith("data:") || userInfo.value.avatar.startsWith("http")) {
        return userInfo.value.avatar;
      }
      return `${userInfo.value.avatar}?t=${avatarTimestamp.value}`;
    }
    const seed = userInfo.value?.username || "default";
    return `https://api.dicebear.com/7.x/avataaars/svg?seed=${seed}`;
  });

  const login = async (credentials: LoginCredentials) => {
    const res = await loginApi(credentials);
    if ((res as any).data) {
      token.value = (res as any).data.token || "";
      userInfo.value = (res as any).data.user || (res as any).data;
      localStorage.setItem("token", token.value);
      localStorage.setItem("user", JSON.stringify(userInfo.value));
      const signKey = (res as any).data.signKey;
      if (signKey) localStorage.setItem("signKey", signKey);
    }
    return res;
  };

  const logout = () => {
    token.value = "";
    userInfo.value = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("signKey");
  };

  const updateUser = (newInfo: UserInfo) => {
    userInfo.value = newInfo;
    localStorage.setItem("user", JSON.stringify(newInfo));
  };

  loadUserFromStorage();

  return {
    userInfo,
    token,
    isLoggedIn,
    displayName,
    avatarUrl,
    login,
    logout,
    updateUser,
    loadUserFromStorage,
  };
});
