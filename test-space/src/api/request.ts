import axios, { AxiosError } from "axios";
import { useUserStore } from "@/stores/user";
import router from "@/router";

const REFRESH_THRESHOLD_MS = 24 * 60 * 60 * 1000;
let refreshingPromise: Promise<string> | null = null;

function getTokenExp(token: string): number {
  if (!token) return 0;
  try {
    const payload = token.split(".")[1];
    if (!payload) return 0;
    const json = JSON.parse(
      decodeURIComponent(
        atob(payload.replace(/-/g, "+").replace(/_/g, "/"))
          .split("")
          .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
          .join("")
      )
    );
    return Number(json.exp || 0);
  } catch {
    return 0;
  }
}

function doRefresh(): Promise<string> {
  if (refreshingPromise) return refreshingPromise;
  const oldToken = localStorage.getItem("token");
  if (!oldToken) return Promise.reject(new Error("no token"));
  refreshingPromise = axios({
    url: "/api/auth/refresh",
    method: "post",
    headers: { Authorization: `Bearer ${oldToken}` },
    timeout: 10000,
  })
    .then((resp) => {
      const newToken = resp?.data?.data?.token;
      if (newToken) {
        localStorage.setItem("token", newToken);
        return newToken;
      }
      throw new Error("refresh response missing token");
    })
    .finally(() => {
      refreshingPromise = null;
    });
  return refreshingPromise;
}

const request = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

request.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    const url = config.url || "";
    const skipRefresh =
      url.includes("/auth/login") ||
      url.includes("/auth/logout") ||
      url.includes("/auth/refresh");
    if (!skipRefresh) {
      const exp = getTokenExp(token);
      if (exp > 0) {
        const remainMs = exp * 1000 - Date.now();
        if (remainMs > 0 && remainMs < REFRESH_THRESHOLD_MS) {
          doRefresh().catch(() => {});
        }
      }
    }
    const signKey = localStorage.getItem("signKey");
    if (signKey) {
      const ts = Date.now().toString();
      const nonce = Math.random().toString(36).substring(2, 10);
      const path = (config.url || "").startsWith("/")
        ? config.url
        : "/" + config.url;
      const sign = btoa(ts + nonce + path + signKey);
      config.headers["X-Timestamp"] = ts;
      config.headers["X-Nonce"] = nonce;
      config.headers["X-Sign"] = sign;
    }
  }
  return config;
});

request.interceptors.response.use(
  (response) => {
    const res = response.data;
    if (response.config?.responseType === "blob") return response;
    if (res.code !== 200) {
      if (res.code === 409) return res;
      return Promise.reject(new Error(res.message || "Request failed"));
    }
    return res;
  },
  async (error: AxiosError) => {
    const config = error.config as any;
    const isLoginRequest = config?.url?.includes("/auth/login");
    if (error.response) {
      const status = error.response.status;
      const detail = (error.response.data as any)?.detail || (error.response.data as any)?.message;
      if (status === 401) {
        if (isLoginRequest) {
          return Promise.reject(new Error(detail || "Invalid username or password"));
        }
        if (config && !config._retriedAfterRefresh && localStorage.getItem("token")) {
          config._retriedAfterRefresh = true;
          try {
            const newToken = await doRefresh();
            if (newToken) {
              config.headers.Authorization = `Bearer ${newToken}`;
              return request(config);
            }
          } catch {}
        }
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        router.push("/login");
        return Promise.reject(new Error("Session expired"));
      }
      if (status === 403) {
        return Promise.reject(new Error(detail || "No permission"));
      }
      return Promise.reject(new Error(detail || error.message || "Request failed"));
    }
    return Promise.reject(error);
  }
);

export default request;
