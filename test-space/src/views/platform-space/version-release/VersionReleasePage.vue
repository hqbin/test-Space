<template>
  <div>
    <div class="flex justify-between items-end mb-8">
      <div>
        <h2 class="font-display-lg text-display-lg font-semibold text-on-surface tracking-tight">Version Release</h2>
        <p class="font-body-lg text-body-lg text-on-surface-variant mt-2">Manage version releases and publish notes.</p>
      </div>
      <button class="glass-button px-6 py-2 rounded-full font-label-md text-label-md flex items-center gap-2" @click="showEditor = true">
        <span class="material-symbols-outlined text-[18px]">add</span>
        New Version
      </button>
    </div>

    <div class="flex flex-col gap-4">
      <div v-for="version in versions" :key="version.id" class="glass-card rounded-xl p-6">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-primary-fixed flex items-center justify-center text-on-primary-fixed font-bold font-headline-md">
              {{ version.version.slice(0, 2) }}
            </div>
            <div>
              <div class="flex items-center gap-3">
                <h3 class="font-headline-md text-headline-md text-on-surface font-semibold">{{ version.version }}</h3>
                <span
                  class="px-2.5 py-0.5 rounded-full font-caption text-caption"
                  :class="version.status === 'published' ? 'bg-success-indicator/10 text-success-indicator border border-success-indicator/20' : 'bg-surface-variant text-on-surface-variant border border-outline-variant/30'"
                >
                  {{ version.status === 'published' ? 'Published' : 'Draft' }}
                </span>
              </div>
              <p class="font-body-md text-body-md text-on-surface-variant mt-1">{{ version.title }}</p>
            </div>
          </div>
          <div class="flex gap-2">
            <button
              v-if="version.status === 'draft'"
              class="glass-button px-4 py-1.5 rounded-full font-caption text-caption flex items-center gap-1"
              @click="publishVersion(version)"
            >
              <span class="material-symbols-outlined text-[14px]">publish</span>
              Publish
            </button>
            <button class="glass-button text-on-surface-variant p-1 rounded">
              <span class="material-symbols-outlined text-[18px]">more_vert</span>
            </button>
          </div>
        </div>

        <div class="mt-4 pl-16">
          <div v-for="(item, idx) in version.changelog" :key="idx" class="flex items-start gap-3 py-1">
            <span
              class="px-2 py-0.5 rounded text-[10px] font-semibold uppercase min-w-[60px] text-center"
              :class="changeTypeClass(item.type)"
            >
              {{ item.type }}
            </span>
            <span class="font-body-md text-body-md text-on-surface-variant">{{ item.content }}</span>
          </div>
        </div>

        <div class="mt-4 pt-4 border-t border-glass-border-dark flex items-center justify-between font-caption text-caption text-on-surface-variant">
          <span>Created {{ version.createdAt }}</span>
          <span v-if="version.status === 'published'">Published {{ version.publishedAt }}</span>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showEditor" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="showEditor = false">
        <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
        <div class="glass-panel rounded-[2rem] p-8 w-full max-w-lg relative z-10 bg-white/60 max-h-[80vh] overflow-y-auto">
          <h3 class="font-headline-md text-headline-md text-on-surface font-semibold mb-6">New Version Release</h3>
          <div class="flex flex-col gap-4">
            <div>
              <label class="block font-label-md text-caption text-on-surface uppercase tracking-wider mb-2">Version</label>
              <input v-model="newVersion.version" class="w-full bg-white border border-outline-variant rounded-lg px-4 py-3 text-body-md text-on-surface focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all" placeholder="v2.1.0" />
            </div>
            <div>
              <label class="block font-label-md text-caption text-on-surface uppercase tracking-wider mb-2">Title</label>
              <input v-model="newVersion.title" class="w-full bg-white border border-outline-variant rounded-lg px-4 py-3 text-body-md text-on-surface focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all" placeholder="Payment Gateway Refactor" />
            </div>
            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="block font-label-md text-caption text-on-surface uppercase tracking-wider">Changelog</label>
                <button class="glass-button font-caption text-caption flex items-center gap-1" @click="addChangelogItem">
                  <span class="material-symbols-outlined text-[14px]">add</span>
                  Add item
                </button>
              </div>
              <div v-for="(item, idx) in newVersion.changelog" :key="idx" class="flex gap-2 mb-2">
                <select v-model="item.type" class="bg-white border border-outline-variant rounded-lg px-3 py-2 text-body-md text-on-surface focus:ring-2 focus:ring-secondary/30 focus:border-secondary">
                  <option value="new">New</option>
                  <option value="fix">Fix</option>
                  <option value="improve">Improve</option>
                  <option value="delete">Delete</option>
                </select>
                <input v-model="item.content" class="flex-1 bg-white border border-outline-variant rounded-lg px-3 py-2 text-body-md text-on-surface focus:ring-2 focus:ring-secondary/30 focus:border-secondary" placeholder="Description" />
                <button class="glass-button text-on-surface-variant" @click="removeChangelogItem(idx)">
                  <span class="material-symbols-outlined text-[18px]">remove_circle</span>
                </button>
              </div>
            </div>
            <button class="w-full glass-button font-label-md text-label-md py-3 rounded-full" @click="saveVersion">
              Create Version
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { fetchVersions, createVersion as apiCreateVersion, publishVersion as apiPublishVersion, type VersionRelease, type ChangelogItem, type CreateVersionPayload } from "@/api/version-releases";

const showEditor = ref(false);

const newVersion = ref<CreateVersionPayload>({
  version: "",
  title: "",
  changelog: [{ type: "new", content: "" }],
});

const versions = ref<VersionRelease[]>([]);

function changeTypeClass(type: string) {
  switch (type) {
    case "new": return "bg-success-indicator/20 text-success-indicator";
    case "fix": return "bg-tertiary-fixed text-on-tertiary-fixed";
    case "improve": return "bg-primary-fixed text-on-primary-fixed";
    case "delete": return "bg-error-container text-on-error-container";
    default: return "bg-surface-variant text-on-surface-variant";
  }
}

function addChangelogItem() {
  newVersion.value.changelog.push({ type: "new", content: "" });
}

function removeChangelogItem(idx: number) {
  newVersion.value.changelog.splice(idx, 1);
}

async function saveVersion() {
  const payload: CreateVersionPayload = {
    version: newVersion.value.version || "v" + (versions.value.length + 1) + ".0.0",
    title: newVersion.value.title || "Untitled Release",
    changelog: newVersion.value.changelog.filter((c) => c.content.trim()),
  };
  try {
    const created = await apiCreateVersion(payload);
    versions.value.unshift(created);
  } catch {
    versions.value.unshift({
      id: Date.now(),
      ...payload,
      status: "draft",
      createdAt: new Date().toISOString().slice(0, 10),
    });
  }
  showEditor.value = false;
  newVersion.value = { version: "", title: "", changelog: [{ type: "new", content: "" }] };
}

async function publishVersion(version: VersionRelease) {
  try {
    const updated = await apiPublishVersion(version.id);
    Object.assign(version, updated);
  } catch {
    version.status = "published";
    version.publishedAt = new Date().toISOString().slice(0, 10);
  }
}

onMounted(async () => {
  try {
    versions.value = await fetchVersions();
  } catch {
    versions.value.push({
      id: 1,
      version: "v2.1.0",
      title: "Payment Gateway Refactor",
      status: "published",
      changelog: [
        { type: "new", content: "Added Stripe integration for payment processing" },
        { type: "fix", content: "Fixed currency conversion rounding error" },
        { type: "improve", content: "Optimized checkout flow performance" },
      ],
      createdAt: "2026-06-10",
      publishedAt: "2026-06-12",
    }, {
      id: 2,
      version: "v2.2.0",
      title: "Authentication Overhaul",
      status: "draft",
      changelog: [
        { type: "new", content: "OAuth 2.0 with PKCE support" },
        { type: "delete", content: "Deprecated v1 auth endpoints" },
      ],
      createdAt: "2026-06-13",
    });
  }
});
</script>
