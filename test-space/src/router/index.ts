import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/auth/Login.vue"),
      meta: { public: true },
    },
    {
      path: "/",
      component: () => import("@/layouts/AppLayout.vue"),
      meta: { requiresAuth: true },
      children: [
        { path: "", redirect: "/workspace" },
        {
          path: "workspace",
          name: "workspace",
          component: () => import("@/views/workspace/WorkspacePage.vue"),
        },
        {
          path: "case-space",
          component: () => import("@/layouts/CaseSpaceLayout.vue"),
          children: [
            { path: "", name: "case-space", component: () => import("@/views/case-space/CaseSpacePage.vue") },
            { path: "editor", name: "case-editor", component: () => import("@/views/case-space/editor/CaseEditorPage.vue") },
            { path: "field-rules", name: "case-field-rules", component: () => import("@/views/case-space/field-rules/FieldRulesPage.vue") },
          ],
        },
        {
          path: "device-space",
          name: "device-space",
          component: () => import("@/views/device-space/DeviceSpacePage.vue"),
        },
        {
          path: "notes-space",
          name: "notes-space",
          component: () => import("@/views/note-space/NotesSpacePage.vue"),
        },
        {
          path: "platform-space",
          component: () => import("@/layouts/PlatformLayout.vue"),
          children: [
            { path: "", redirect: "/platform-space/analytics" },
            {
              path: "analytics",
              name: "platform-analytics",
              component: () => import("@/views/platform-space/analytics/AnalyticsPage.vue"),
            },
            {
              path: "database",
              name: "platform-database",
              component: () => import("@/views/platform-space/database/DatabasePage.vue"),
            },
            {
              path: "version-release",
              name: "platform-version-release",
              component: () => import("@/views/platform-space/version-release/VersionReleasePage.vue"),
            },
          ],
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

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("token");
  if (to.meta.requiresAuth && !token) {
    next({ path: "/login", query: { redirect: to.fullPath } });
  } else if (to.path === "/login" && token) {
    next({ path: "/workspace" });
  } else {
    next();
  }
});

export default router;
