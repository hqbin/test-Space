import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: () => import("@/layouts/AppLayout.vue"),
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
