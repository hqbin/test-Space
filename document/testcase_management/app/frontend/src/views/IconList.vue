<template>
  <div class="icon-list">
    <h1>Element Plus Icons List</h1>
    <div class="icon-grid">
      <div v-for="(icon, name) in icons" :key="name" class="icon-item">
        <el-icon :size="24"><component :is="icon" /></el-icon>
        <span>{{ name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import * as ElIcons from '@element-plus/icons-vue'

const icons = ElIcons
</script>

<style scoped>
.icon-list {
  padding: 20px;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  border: 1px solid #eaeaea;
  border-radius: 8px;
  transition: all 0.3s;
}

.icon-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.icon-item el-icon {
  margin-bottom: 10px;
  color: #8b9aee;
}

.icon-item span {
  font-size: 12px;
  color: #606266;
  text-align: center;
}
</style>