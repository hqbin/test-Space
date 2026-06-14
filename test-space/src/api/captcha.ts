import request from "./request";
import type { ApiResponse, CaptchaResponse } from "@/types";

export const getCaptcha = () =>
  request.get("/captcha") as Promise<ApiResponse<CaptchaResponse["data"]>>;
