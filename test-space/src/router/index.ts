import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/mirror",
      name: "standalone-mirror",
      component: () => import("@/views/device-space/StandaloneMirror.vue"),
    },
    {
      path: "/",
      component: () => import("@/layouts/AppLayout.vue"),
      children: [
        { path: "", redirect: "/device-space" },
        {
          path: "device-space",
          name: "device-space",
          component: () => import("@/views/device-space/DeviceSpacePage.vue"),
        },
        {
          path: "device-space/perf-monitor",
          name: "perf-monitor",
          component: () => import("@/views/device-space/PerfMonitorPage.vue"),
        },
        {
          path: "notes-space",
          name: "notes-space",
          component: () => import("@/views/note-space/NotesSpacePage.vue"),
        },
        {
          path: "api-space",
          name: "api-space",
          component: () => import("@/views/api-space/ApiSpacePage.vue"),
        },
        {
          path: "script-space",
          name: "script-space",
          component: () => import("@/views/script-space/ScriptSpacePage.vue"),
        },
        {
          path: "settings",
          name: "settings",
          component: () => import("@/views/settings/SettingsPage.vue"),
        },
      ],
    },
  ],
});

export default router;
