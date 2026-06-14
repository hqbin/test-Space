import request from "./request";
import type { LoginCredentials } from "@/types";

export const login = (data: LoginCredentials) =>
  request({ url: "/auth/login", method: "post", data });

export const logout = () =>
  request({ url: "/auth/logout", method: "post" });

export const refreshToken = () =>
  request({ url: "/auth/refresh", method: "post", _isRefresh: true } as any);

export const registerUser = (data: Record<string, unknown>) =>
  request({ url: "/auth/register", method: "post", data });
