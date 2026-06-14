<template>
  <div class="flex flex-col min-h-full">
    <!-- Header -->
    <header class="mt-12 mb-16">
      <h2 class="font-display-lg text-display-lg text-on-surface font-black tracking-tighter">
        Good {{ greeting }}, {{ userStore.displayName }}.
      </h2>
      <p class="font-headline-md text-headline-md text-on-surface-variant mt-4">
        What would you like to do today?
      </p>

      <!-- Command Center -->
      <div class="mt-8 relative max-w-4xl glass-panel rounded-full p-2 flex items-center recessed-input bg-white/40">
        <span class="material-symbols-outlined text-primary ml-4 mr-2">search</span>
        <input
          class="flex-1 bg-transparent border-none outline-none font-body-lg text-body-lg text-on-surface placeholder:text-on-surface-variant/60 px-2 py-3 focus:ring-0"
          placeholder="Type a command, search projects, or ask a question..."
          type="text"
        />
        <button
          class="glass-button px-6 py-2 rounded-full font-label-md text-label-md"
        >
          Execute
        </button>
      </div>
    </header>

    <!-- Quick Actions -->
    <section class="grid grid-cols-1 md:grid-cols-3 gap-gutter-grid mb-16">
      <button
        v-for="action in quickActions"
        :key="action.title"
        class="glass-button rounded-xl p-padding-card flex flex-col items-start gap-4 text-left group cursor-pointer"
      >
        <div
          class="w-12 h-12 rounded-full bg-secondary-fixed text-on-secondary-fixed-variant flex items-center justify-center group-hover:scale-110 transition-transform"
        >
          <span class="material-symbols-outlined">{{ action.icon }}</span>
        </div>
        <div>
          <h3 class="font-headline-md text-headline-md text-on-surface group-hover:text-secondary">{{ action.title }}</h3>
          <p class="font-body-md text-body-md text-on-surface-variant mt-2">{{ action.description }}</p>
        </div>
      </button>
    </section>

    <!-- Continue Working -->
    <section>
      <h3 class="font-headline-lg text-headline-lg text-on-surface font-semibold mb-6">Continue Working</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-gutter-grid">
        <div
          v-for="project in projects"
          :key="project.title"
          class="glass-card rounded-[2rem] p-padding-card relative overflow-hidden group cursor-pointer glass-hover"
        >
          <div
            class="absolute top-6 right-6 flex items-center gap-2 px-3 py-1 rounded-full font-caption text-caption"
            :class="project.running
              ? 'bg-success-indicator/10 text-success-indicator border border-success-indicator/20 shadow-[0_0_10px_rgba(34,197,94,0.2)]'
              : 'bg-surface-variant text-on-surface-variant border border-outline-variant/30'"
          >
            <span
              class="w-2 h-2 rounded-full"
              :class="project.running ? 'bg-success-indicator animate-pulse' : 'bg-outline'"
            />
            {{ project.running ? "Running" : "Paused" }}
          </div>
          <div class="w-14 h-14 rounded-2xl bg-white/40 border border-white/60 flex items-center justify-center mb-6 shadow-sm">
            <span class="material-symbols-outlined text-2xl" :class="project.running ? 'text-primary' : 'text-tertiary'">
              {{ project.icon }}
            </span>
          </div>
          <h4 class="font-headline-md text-headline-md text-on-surface mb-2">{{ project.title }}</h4>
          <p class="font-body-md text-body-md text-on-surface-variant mb-6">{{ project.description }}</p>
          <div class="flex items-center justify-between border-t border-glass-border-dark pt-4">
            <span class="font-caption text-caption text-on-surface-variant">Last edited {{ project.time }}</span>
            <div class="flex -space-x-2">
              <div
                v-for="(initial, idx) in project.members"
                :key="idx"
                class="w-8 h-8 rounded-full flex items-center justify-center border-2 border-surface font-caption text-caption"
                :class="memberColors[idx % memberColors.length]"
              >
                {{ initial }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { useUserStore } from "@/stores/user";
import { fetchDashboardStats, fetchQuickActions, fetchProjects, type QuickAction, type ProjectItem } from "@/api/dashboard";

const userStore = useUserStore();

const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 12) return "Morning";
  if (hour < 18) return "Afternoon";
  return "Evening";
});

const quickActions = ref<QuickAction[]>([
  { icon: "science", title: "Generate Test Cases", description: "AI-assisted test generation based on recent commits." },
  { icon: "analytics", title: "Analyze Logs", description: "Deep dive into recent system anomalies and performance drops." },
  { icon: "devices", title: "Provision Device", description: "Setup a new virtual environment or physical hardware target." },
]);

const projects = ref<ProjectItem[]>([
  { title: "Core Migration Alpha", description: "Database schema updates and data integrity validation scripts.", icon: "database", running: true, time: "2h ago", members: ["JD", "AS"] },
  { title: "Payment Gateway Refactor", description: "Updating legacy endpoints to v3 API specifications.", icon: "api", running: false, time: "yesterday", members: ["ME"] },
]);

const memberColors = [
  "bg-primary-fixed text-on-primary-fixed-variant",
  "bg-tertiary-fixed text-on-tertiary-fixed-variant",
  "bg-secondary-fixed text-on-secondary-fixed-variant",
];

onMounted(async () => {
  try {
    const [actions, projectData] = await Promise.all([
      fetchQuickActions(),
      fetchProjects(),
    ]);
    quickActions.value = actions;
    projects.value = projectData;
  } catch {}
});
</script>
