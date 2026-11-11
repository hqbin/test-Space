<template>
  <div class="h-full flex gap-4 min-h-0">
    <!-- 左侧：媒体（Media）下拉 + 广告位 -->
    <aside class="w-[322px] shrink-0 glass-panel rounded-xl flex flex-col min-h-0 overflow-hidden">
      <div class="px-3 pt-3 pb-2.5 flex flex-col gap-1.5 shrink-0">
        <div class="flex items-center gap-1.5">
          <span class="material-symbols-outlined text-[15px] text-secondary">apps</span>
          <span class="text-[12px] font-semibold text-on-surface">{{ t('backend.media') }}</span>
          <span class="text-[10px] text-on-surface-variant">{{ t('backend.mediaTotal', { n: String(mediaTotal) }) }}</span>
          <button class="ml-auto material-symbols-outlined text-[14px] text-on-surface-variant hover:text-secondary disabled:opacity-40"
            :class="mediaBusy ? 'animate-spin' : ''" :title="t('backend.refresh')" :disabled="mediaBusy" @click="loadMedias()">refresh</button>
        </div>
        <SearchSelect :model-value="selectedMediaId" :options="mediaOptions" :loading="mediaBusy"
          :placeholder="t('backend.selectMedia')" :search-placeholder="t('backend.searchMedia')"
          :empty-text="t('backend.noData')" @update:model-value="onMediaChange" />
        <div class="text-[10px] text-on-surface-variant truncate">
          <template v-if="selectedMedia">#{{ selectedMedia.id }} · {{ zones.length }} {{ t('backend.zone') }}</template>
          <template v-else>{{ t('backend.selectMedia') }}</template>
        </div>
      </div>

      <div class="border-t border-hairline/60 flex-1 min-h-0 flex flex-col px-2 py-2">
        <div class="px-1 pb-1.5 flex items-center justify-between shrink-0">
          <span class="text-[12px] font-semibold text-on-surface">{{ t('backend.zone') }}</span>
          <span class="flex items-center gap-1.5 text-[10px] text-on-surface-variant">
            <span v-if="zonesBusy" class="w-2.5 h-2.5 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
            {{ zones.length }}
          </span>
        </div>
        <div class="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-0.5">
          <button class="text-left px-2.5 py-1.5 rounded-lg text-[11px] glass-hover shrink-0"
            :class="selectedZoneId === '' ? 'glass-active font-semibold' : 'text-on-surface-variant'"
            @click="selectZone('')">{{ t('backend.allZones') }}</button>
          <button v-for="z in zones" :key="z.id"
            class="text-left px-2.5 py-1.5 rounded-lg text-[11px] glass-hover flex items-start justify-between gap-1.5"
            :class="selectedZoneId === z.id ? 'glass-active font-semibold' : 'text-on-surface-variant'"
            @click="selectZone(z.id)">
            <span class="min-w-0 break-words leading-[1.35]">{{ z.name }}</span>
            <span class="text-[10px] opacity-60 shrink-0 font-mono">#{{ z.id }}</span>
          </button>
          <div v-if="!zones.length" class="px-2 py-3 text-[11px] text-on-surface-variant text-center">
            <span v-if="zonesBusy" class="inline-flex items-center gap-1.5">
              <span class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
              {{ t('backend.loading') }}
            </span>
            <template v-else>{{ selectedMediaId ? t('backend.noData') : t('backend.selectMedia') }}</template>
          </div>
        </div>
      </div>
    </aside>

    <!-- 右侧 -->
    <section class="flex-1 min-w-0 flex flex-col gap-2.5 min-h-0">
      <!-- 工具栏 -->
      <div class="glass-panel rounded-xl px-3 py-2 flex flex-wrap items-center gap-2 shrink-0">
        <div class="relative shrink-0">
          <input v-model="adKeyword" class="glass-input pl-2.5 pr-7 py-1.5 rounded-lg text-[11px] w-[190px] select-text"
            :placeholder="t('backend.searchAd')" @input="onSearchInput" @keyup.enter="applySearch" />
          <button v-if="adKeyword" class="absolute right-1.5 top-1/2 -translate-y-1/2 material-symbols-outlined text-[13px] text-on-surface-variant hover:text-secondary"
            :title="t('backend.clearSearch')" @click="clearSearch">close</button>
        </div>
        <button class="glass-button rounded-lg px-2.5 py-1.5 text-[11px] flex items-center gap-1" :disabled="ordersBusy" @click="reloadAds">
          <span v-if="ordersBusy" class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
          <span v-else class="material-symbols-outlined text-[14px]">refresh</span>{{ t('backend.query') }}
        </button>
        <div class="h-5 w-[1px] bg-glass-border-dark"></div>
        <button v-if="canWrite" class="glass-button rounded-lg px-2.5 py-1.5 text-[11px] flex items-center gap-1" @click="openNewAd">
          <span class="material-symbols-outlined text-[14px]">add</span>{{ t('backend.newAd') }}
        </button>
        <button class="glass-button rounded-lg px-2.5 py-1.5 text-[11px] flex items-center gap-1" @click="openVerify">
          <span class="material-symbols-outlined text-[14px]">fact_check</span>{{ t('backend.verifyEntry') }}
          <span v-if="pendingCount" class="text-[10px] px-1.5 rounded-full bg-secondary/15 text-secondary">{{ pendingCount }}</span>
        </button>
        <button class="glass-button rounded-lg px-2.5 py-1.5 text-[11px] flex items-center gap-1" @click="ceOpen = true">
          <span class="material-symbols-outlined text-[14px]">tune</span>{{ t('backend.ceManage') }}
        </button>
        <!-- 环境 + 登出：靠右，与 Custom engine 同一行 -->
        <div class="ml-auto flex items-center gap-1.5 shrink-0">
          <button class="text-[10px] font-semibold tracking-wider px-2 py-0.5 rounded-full bg-secondary/10 text-secondary hover:bg-secondary/20 select-none"
            :title="t('backend.switchEnv')" @click="emit('switch-env')">{{ envLabel }}</button>
          <button class="icon-action" :title="t('backend.logout')" @click="emit('logout')">
            <span class="material-symbols-outlined text-[15px]">logout</span>
          </button>
        </div>
      </div>

      <!-- MAC 查询 -->
      <div class="glass-panel rounded-xl px-3 py-2 flex flex-wrap items-center gap-2 shrink-0">
        <span class="text-[11px] text-on-surface-variant shrink-0">{{ t('backend.macQuery') }}</span>
        <input v-model="mac" class="glass-input px-2.5 py-1.5 rounded-lg text-[11px] w-[200px] select-text"
          :placeholder="t('backend.macPlaceholder')" @keyup.enter="doMacQuery" />
        <button class="glass-button rounded-lg px-2.5 py-1.5 text-[11px] flex items-center gap-1" :disabled="macBusy" @click="doMacQuery">
          <span v-if="macBusy" class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
          {{ t('backend.query') }}
        </button>
        <span class="ml-auto text-[10px] text-on-surface-variant truncate">{{ t('backend.macHint') }}</span>
      </div>

      <!-- 广告表格 -->
      <div class="glass-panel rounded-xl flex-1 min-h-0 flex flex-col overflow-hidden">
        <div v-if="macMode" class="px-3 py-1.5 border-b border-hairline/60 bg-secondary/5 flex flex-wrap items-center gap-2 shrink-0">
          <span class="material-symbols-outlined text-[13px] text-secondary">filter_alt</span>
          <span class="text-[11px] text-on-surface">
            {{ t('backend.macResult', { mac: mac.trim() || '-', n: String(orders.length) }) }}
          </span>
          <span v-if="macMatched.length" class="text-[10px] px-1.5 py-0.5 rounded-full bg-secondary/10 text-secondary"
            :title="macMatched.map((k) => engineTitle(k)).join('\n')">
            {{ t('backend.ruleHit', { n: String(macMatched.length) }) }}
          </span>
          <button class="ml-auto glass-button rounded-md px-2 py-0.5 text-[10px] flex items-center gap-1" @click="clearMac">
            <span class="material-symbols-outlined text-[12px]">close</span>{{ t('backend.clearResult') }}
          </button>
        </div>
        <div class="grid grid-cols-[56px_1fr_150px_170px_136px] gap-2 px-3 py-2 text-[11px] font-semibold text-on-surface-variant border-b border-hairline/60 shrink-0">
          <span>ID</span>
          <span>{{ t('backend.ads') }}</span>
          <span>Campaign</span>
          <span>{{ t('backend.beginDate') }} ~ {{ t('backend.endDate') }}</span>
          <span class="text-right">{{ t('backend.operation') }}</span>
        </div>
        <div class="relative flex-1 min-h-0">
          <div class="h-full overflow-y-auto custom-scrollbar">
            <div v-for="o in orders" :key="o.id"
              class="grid grid-cols-[56px_1fr_150px_170px_136px] gap-2 px-3 py-1.5 text-[11px] items-center border-b border-hairline/40 hover:bg-secondary/5">
              <span class="font-mono text-graphite truncate">#{{ o.id }}</span>
              <button class="truncate text-left text-secondary hover:underline" :title="o.name" @click="openEdit(o)">{{ o.name }}</button>
              <span class="truncate text-on-surface-variant" :title="campaignName(o)">{{ campaignName(o) }}</span>
              <span class="truncate text-on-surface-variant">{{ shortDate(o.begin_date) }} ~ {{ shortDate(o.end_date) }}</span>
              <span class="flex items-center justify-end gap-0.5">
                <template v-if="canWrite">
                  <button class="icon-action" :title="t('backend.edit')" @click="openEdit(o)">
                    <span class="material-symbols-outlined text-[15px]">edit</span>
                  </button>
                  <button class="icon-action" :title="t('backend.copyAd')" :disabled="copyBusyId === o.id" @click="copyOrder(o)">
                    <span v-if="copyBusyId === o.id" class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
                    <span v-else class="material-symbols-outlined text-[15px]">content_copy</span>
                  </button>
                  <button v-if="canPause(o)" class="icon-action" :title="t('backend.pause')"
                    :disabled="actionBusyId === o.id" @click="askAction(o, 'pause')">
                    <span v-if="actionBusyId === o.id" class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
                    <span v-else class="material-symbols-outlined text-[15px]">pause_circle</span>
                  </button>
                  <button v-else-if="canPlay(o)" class="icon-action" :title="t('backend.play')"
                    :disabled="actionBusyId === o.id" @click="askAction(o, 'play')">
                    <span v-if="actionBusyId === o.id" class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
                    <span v-else class="material-symbols-outlined text-[15px]">play_circle</span>
                  </button>
                  <button class="icon-action is-danger" :title="t('backend.delete')"
                    :disabled="actionBusyId === o.id" @click="askAction(o, 'delete')">
                    <span class="material-symbols-outlined text-[15px]">delete</span>
                  </button>
                </template>
                <span v-else class="text-[10px] text-on-surface-variant">-</span>
              </span>
            </div>
            <div v-if="!orders.length && !ordersBusy" class="h-full flex items-center justify-center text-[12px] text-on-surface-variant">
              {{ macMode ? t('backend.macNoData') : t('backend.noData') }}
            </div>
          </div>
          <div v-if="ordersBusy" class="loading-veil">
            <span class="w-3.5 h-3.5 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
            <span class="text-[11px] text-on-surface-variant">{{ t('backend.loading') }}</span>
          </div>
        </div>
        <div class="flex items-center justify-end gap-2 px-3 py-1.5 border-t border-hairline/60 text-[11px] shrink-0">
          <template v-if="macMode">
            <span class="text-on-surface-variant">{{ orders.length }} {{ t('backend.ads') }}</span>
          </template>
          <template v-else>
            <span class="text-on-surface-variant">{{ total }} {{ t('backend.ads') }}</span>
            <button class="glass-button rounded-md px-2 py-0.5" :disabled="page <= 1 || ordersBusy" @click="changePage(-1)">{{ t('backend.prev') }}</button>
            <span>{{ page }}</span>
            <button class="glass-button rounded-md px-2 py-0.5" :disabled="page * pageSize >= total || ordersBusy" @click="changePage(1)">{{ t('backend.next') }}</button>
          </template>
        </div>
      </div>
    </section>

    <!-- 新建 / 编辑广告 -->
    <Teleport to="body">
      <div v-if="editorOpen" class="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-6">
        <div class="solid-panel rounded-2xl w-[920px] max-h-[92vh] flex flex-col overflow-hidden">
          <div class="panel-bar px-4 py-2.5 flex items-center gap-2 border-b border-hairline/60 shrink-0">
            <span class="material-symbols-outlined text-[16px] text-secondary">{{ editingId ? 'edit' : 'add_box' }}</span>
            <span class="text-[13px] font-semibold">{{ editingId ? t('backend.editAd') : t('backend.newAd') }}</span>
            <span v-if="editingId" class="text-[11px] text-on-surface-variant font-mono">#{{ editingId }}</span>
            <span v-if="metaBusy" class="flex items-center gap-1 text-[10px] text-on-surface-variant">
              <span class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
              {{ t('backend.adTypeLoading') }}
            </span>
            <button class="ml-auto glass-button rounded-md px-2 py-0.5 text-[11px]" @click="closeEditor">{{ t('backend.cancel') }}</button>
          </div>

          <div class="px-4 py-3 flex-1 min-h-0 overflow-y-auto custom-scrollbar flex flex-col gap-3">
            <!-- Campaign -->
            <div class="flex items-center gap-2">
              <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0">Campaign</span>
              <div v-if="!editingId" class="flex rounded-full border border-outline-variant/50 overflow-hidden shrink-0">
                <button class="px-2.5 py-1 text-[11px]" :class="editor.campaignMode === 'existing' ? 'bg-secondary/15 text-secondary font-semibold' : 'text-on-surface-variant'" @click="editor.campaignMode = 'existing'">{{ t('backend.existingCampaign') }}</button>
                <button class="px-2.5 py-1 text-[11px]" :class="editor.campaignMode === 'new' ? 'bg-secondary/15 text-secondary font-semibold' : 'text-on-surface-variant'" @click="editor.campaignMode = 'new'">{{ t('backend.newCampaign') }}</button>
              </div>
              <template v-if="editor.campaignMode === 'existing' || editingId">
                <div class="flex-1 min-w-0">
                  <SearchSelect :model-value="editor.campaignId" :options="campaignOptions"
                    :placeholder="t('backend.selectCampaign')" :search-placeholder="t('backend.searchCampaign')"
                    :empty-text="t('backend.noData')" :loading="campaignsBusy"
                    @update:model-value="onCampaignChange" />
                </div>
              </template>
            </div>
            <div v-if="editor.campaignMode === 'new' && !editingId" class="grid grid-cols-3 gap-2 pl-[112px]">
              <input v-model="editor.campaignName" class="glass-input px-2 py-1 rounded-md text-[11px] select-text" :placeholder="t('backend.campaignName')" />
              <SearchSelect :model-value="editor.advertiserid" :options="advertiserOptions"
                :placeholder="t('backend.advertiser')" :search-placeholder="t('backend.searchAdvertiser')"
                :empty-text="t('backend.noData')" :loading="advertisersBusy"
                @update:model-value="(v: string) => (editor.advertiserid = v)" />
              <input v-model="editor.demandPartner" class="glass-input px-2 py-1 rounded-md text-[11px] select-text" :placeholder="t('backend.demandPartner')" />
            </div>

            <!-- 名称 / 日期 / 优先级 -->
            <div class="grid grid-cols-2 gap-x-3 gap-y-2 items-start">
              <div class="flex items-center gap-2">
                <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0">{{ t('backend.adName') }}</span>
                <input v-model="editor.name" class="glass-input px-2 py-1 rounded-md text-[11px] flex-1 min-w-0 select-text" :placeholder="t('backend.namePlaceholder')" />
              </div>
              <div class="flex items-center gap-2">
                <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0">{{ t('backend.beginDate') }}</span>
                <input v-model="editor.beginDate" type="date" class="glass-input px-2 py-1 rounded-md text-[11px] flex-1 min-w-0" />
              </div>
              <div class="flex items-center gap-2">
                <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0">{{ t('backend.endDate') }}</span>
                <input v-model="editor.endDate" type="date" min="1970-01-01" max="9999-12-31"
                  class="glass-input px-2 py-1 rounded-md text-[11px] flex-1 min-w-0" />
                <div class="flex items-center gap-0.5 shrink-0">
                  <button v-for="p in endDatePresets" :key="p.key"
                    class="px-1.5 py-1 rounded-md text-[10px] border transition-colors"
                    :class="editor.endDate === p.value
                      ? 'border-secondary/50 bg-secondary/10 text-secondary font-semibold'
                      : 'border-outline-variant/50 text-on-surface-variant hover:bg-secondary/5'"
                    :title="p.hint" @click="editor.endDate = p.value">{{ p.label }}</button>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0">{{ t('backend.priority') }}</span>
                <select v-model="editor.adClass" class="glass-input px-2 py-1 rounded-md text-[11px] flex-1 min-w-0">
                  <option v-for="o in priorityOptions" :key="o.v" :value="o.v">{{ o.t }}</option>
                </select>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0">{{ t('backend.priceMode') }}</span>
                <select v-model="editor.priceMode" class="glass-input px-2 py-1 rounded-md text-[11px] flex-1 min-w-0">
                  <option v-for="o in priceModeOptions" :key="o.v" :value="o.v">{{ o.t }}</option>
                </select>
              </div>
              <div class="flex flex-col gap-0.5">
                <div class="flex items-center gap-2">
                  <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0">{{ t('backend.adIcon') }}</span>
                  <div class="flex items-center gap-3">
                    <label class="flex items-center gap-1 text-[11px] cursor-pointer">
                      <input type="radio" class="accent-secondary" value="0" v-model="editor.disableAdflag" />{{ t('backend.adIconShow') }}
                    </label>
                    <label class="flex items-center gap-1 text-[11px] cursor-pointer">
                      <input type="radio" class="accent-secondary" value="1" v-model="editor.disableAdflag" />{{ t('backend.adIconHide') }}
                    </label>
                  </div>
                </div>
                <div class="text-[10px] text-on-surface-variant pl-[112px]">{{ t('backend.adIconHint') }}</div>
              </div>
            </div>

            <!-- Ad type：与后台一致的三级下拉（选项全部来自接口字典） -->
            <div class="flex items-start gap-2">
              <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0 pt-3.5">{{ t('backend.adType') }}</span>
              <div class="flex flex-col gap-1 min-w-0 flex-1">
                <div class="flex items-end gap-1.5 flex-wrap">
                  <div class="flex flex-col gap-0.5">
                    <span class="text-[9px] text-on-surface-variant pl-0.5">{{ t('backend.adTypeL1') }}</span>
                    <select class="glass-input px-1.5 py-1 rounded-md text-[11px] w-[150px]" :value="editor.adTypeL1"
                      :disabled="metaBusy || !adTypes.length" @change="onL1Change(($event.target as HTMLSelectElement).value)">
                      <option v-for="o in l1List" :key="o.value" :value="o.value">{{ o.label }}</option>
                    </select>
                  </div>
                  <div class="flex flex-col gap-0.5">
                    <span class="text-[9px] text-on-surface-variant pl-0.5">{{ t('backend.adTypeL2') }}</span>
                    <select class="glass-input px-1.5 py-1 rounded-md text-[11px] w-[150px]" :value="editor.adTypeL2"
                      :disabled="metaBusy || !l2List.length" @change="onL2Change(($event.target as HTMLSelectElement).value)">
                      <option v-for="o in l2List" :key="o.value" :value="o.value">{{ o.label }}</option>
                    </select>
                  </div>
                  <div class="flex flex-col gap-0.5">
                    <span class="text-[9px] text-on-surface-variant pl-0.5">{{ t('backend.adTypeL3') }}</span>
                    <select class="glass-input px-1.5 py-1 rounded-md text-[11px] w-[150px]" :value="editor.adTypeL3"
                      :disabled="metaBusy || !l3List.length" @change="onL3Change(($event.target as HTMLSelectElement).value)">
                      <option v-for="o in l3List" :key="o.value" :value="o.value">{{ o.label }}</option>
                    </select>
                  </div>
                  <span v-if="metaBusy" class="w-3 h-3 mb-2 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
                  <span class="text-[10px] text-on-surface-variant ml-1 mb-1">{{ t('backend.adTypeHint') }}</span>
                </div>
                <span v-if="metaError" class="text-[10px] text-error">{{ metaError }}</span>
                <span v-if="adTypeUnknown" class="text-[10px] text-amber-700">
                  {{ t('backend.currentAdType') }}: {{ editor.adType }}（{{ t('backend.adTypeUnknown') }}）
                </span>
              </div>
            </div>

            <!-- Click URL -->
            <div class="flex items-start gap-2">
              <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0 pt-1.5">{{ t('backend.clickUrl') }}</span>
              <LandingInput v-model="editor.clickUrl" />
            </div>

            <!-- Is external -->
            <div class="flex items-start gap-2">
              <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0 pt-1">{{ t('backend.isExternal') }}</span>
              <div class="flex flex-col gap-1">
                <div class="flex items-center gap-3">
                  <label class="flex items-center gap-1 text-[11px] cursor-pointer">
                    <input type="radio" class="accent-secondary" value="0" v-model="editor.external" />{{ t('backend.no') }}
                  </label>
                  <label class="flex items-center gap-1 text-[11px] cursor-pointer">
                    <input type="radio" class="accent-secondary" value="1" v-model="editor.external" />{{ t('backend.yes') }}
                  </label>
                  <select v-if="editor.external === '1'" v-model="editor.adFormat" class="glass-input px-2 py-1 rounded-md text-[11px] w-[170px]">
                    <option value="">{{ t('backend.adFormat') }}</option>
                    <option v-for="f in adFormatOptions" :key="f" :value="f">{{ f }}</option>
                  </select>
                </div>
                <span v-if="editor.external === '1'" class="text-[10px] text-on-surface-variant">{{ t('backend.externalHint') }}</span>
              </div>
            </div>

            <!-- 素材 -->
            <div class="flex flex-col gap-1.5">
              <div class="flex items-center gap-2">
                <span class="text-[11px] font-semibold">{{ t('backend.material') }}</span>
                <span class="text-[10px] text-on-surface-variant">{{ selectedAdTypeHint }}</span>
              </div>
              <div v-for="f in editorFields" :key="f.key" class="flex items-center gap-2 py-0.5">
                <span class="text-[11px] font-mono text-graphite w-[88px] shrink-0 truncate">{{ f.key }}</span>
                <span class="text-[10px] text-on-surface-variant w-[130px] shrink-0 truncate" :title="fieldMeta(f)">{{ fieldMeta(f) }}</span>
                <select v-if="presetsForField(f).length" class="glass-input px-1 py-1 rounded-md text-[10px] w-[110px] shrink-0"
                  :value="''" @change="applyPreset(f.key, $event)">
                  <option value="">{{ t('backend.preset') }}</option>
                  <option v-for="p in presetsForField(f)" :key="p.id" :value="p.id">{{ presetLabel(p) }}</option>
                </select>
                <input v-model="editor.material[f.key]" class="glass-input px-2 py-1 rounded-md text-[10px] font-mono flex-1 min-w-0 select-text" :placeholder="f.key" />
                <button class="glass-button rounded-md px-2 py-0.5 text-[10px] flex items-center gap-1" :disabled="editorUploading === f.key" @click="pickEditorFile(f.key)">
                  <span v-if="editorUploading === f.key" class="w-2.5 h-2.5 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
                  {{ t('backend.upload') }}
                </button>
                <input :ref="(el) => setEditorInput(f.key, el)" type="file" class="hidden" accept="image/*,video/*,application/*" @change="uploadEditorField(f.key, $event)" />
                <a v-if="editorPreview[f.key]" :href="editorPreview[f.key]" target="_blank" class="text-[10px] text-secondary truncate max-w-[90px]">{{ t('backend.preview') }}</a>
              </div>
              <div v-if="!editorFields.length && !metaBusy" class="text-[10px] text-on-surface-variant">{{ t('backend.noMaterialFields') }}</div>
            </div>

            <!-- Assigned media：随 Campaign / 广告类型变化 -->
            <div class="flex flex-col gap-1.5">
              <div class="flex items-center gap-2">
                <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0">{{ t('backend.assignedMedia') }}</span>
                <span class="text-[10px] text-on-surface-variant">{{ t('backend.mediaOptionsHint') }}</span>
              </div>
              <CheckGrid :model-value="editorAppIds" :items="editorApps" :loading="editorAppsBusy"
                :empty-text="t('backend.noData')" :search-placeholder="t('backend.searchMedia')"
                :all-label="t('backend.allZonesShort')" :clear-label="t('backend.clearAll')"
                :select-filtered-label="t('backend.selectFiltered')"
                @update:model-value="onAppsChange" />
            </div>

            <!-- Assigned zone：只显示所选媒体下的广告位 -->
            <div class="flex flex-col gap-1.5">
              <div class="flex items-center gap-2">
                <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0">{{ t('backend.assignedZone') }}</span>
                <span class="text-[10px] text-on-surface-variant">
                  {{ editorAppIds.length ? t('backend.zoneFollowMedia') : t('backend.zoneNeedMedia') }}
                </span>
              </div>
              <CheckGrid :model-value="editorZoneIds" :items="editorZones" :loading="editorZonesBusy"
                :empty-text="editorAppIds.length ? t('backend.noData') : t('backend.zoneNeedMedia')"
                :search-placeholder="t('backend.searchZone')"
                :all-label="t('backend.allZonesShort')" :clear-label="t('backend.clearAll')"
                :select-filtered-label="t('backend.selectFiltered')"
                @update:model-value="onZonesChange" />
            </div>

            <!-- Custom engine（指定 MAC） -->
            <div class="flex flex-col gap-1.5">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-[11px] text-on-surface-variant w-[104px] shrink-0">{{ t('backend.macTarget') }}</span>
                <input v-model="keywordQuery" class="glass-input px-2 py-1 rounded-md text-[11px] w-[200px] select-text"
                  :placeholder="t('backend.keywordSearch')" @keyup.enter="doKeywordSearch" />
                <button class="glass-button rounded-md px-2 py-0.5 text-[11px] flex items-center gap-1"
                  :disabled="keywordBusy" @click="doKeywordSearch">
                  <span v-if="keywordBusy" class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
                  {{ t('backend.query') }}
                </button>
                <button class="glass-button rounded-md px-2 py-0.5 text-[11px] flex items-center gap-1"
                  @click="openEngineDialog">
                  <span class="material-symbols-outlined text-[13px]">tune</span>{{ t('backend.ceManage') }}
                </button>
                <span v-if="!editorKeywords.length && !keywordResults.length" class="text-[10px] text-on-surface-variant">
                  {{ t('backend.keywordOptional') }}
                </span>
              </div>

              <!-- 已选规则 -->
              <div v-if="editorKeywords.length" class="glass-panel rounded-lg px-2 py-1.5 flex flex-wrap gap-1">
                <span v-for="k in editorKeywords" :key="k.id"
                  class="text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1 max-w-[300px]"
                  :class="isUnresolved(k) ? 'bg-amber-500/15 text-amber-700' : 'bg-secondary/10 text-secondary'">
                  <span class="truncate" :title="engineTitle(k)">{{ engineTitle(k) }}</span>
                  <button class="material-symbols-outlined text-[12px] shrink-0" @click="removeKeyword(k.id)">close</button>
                </span>
              </div>
              <span v-if="editorCampaignKeyword" class="text-[10px] text-amber-700">
                {{ t('backend.campaignKeywordHint', { v: editorCampaignKeyword }) }}
              </span>
              <span v-if="editorKeywords.length" class="text-[10px] text-on-surface-variant">
                {{ t('backend.macNeedsCustom') }}
              </span>
              <span v-else-if="editingInheritCampaign" class="text-[10px] text-amber-700">
                {{ t('backend.macInheritNow') }}
              </span>

              <!-- 搜索结果 -->
              <div v-if="keywordResults.length" class="glass-panel rounded-lg p-1.5 flex flex-col gap-0.5 max-h-[130px] overflow-y-auto custom-scrollbar">
                <button v-for="k in keywordResults" :key="k.id" class="text-left text-[10px] px-2 py-1 rounded-md glass-hover flex items-center gap-2"
                  @click="pickKeyword(k)">
                  <span class="font-mono text-graphite shrink-0">#{{ k.id }}</span>
                  <span class="truncate shrink-0 max-w-[140px]">{{ k.valuetext || k.keytext }}</span>
                  <span class="ml-auto opacity-60 font-mono truncate max-w-[320px]">{{ keywordValue(k) }}</span>
                </button>
              </div>
            </div>
          </div>

          <div class="panel-bar px-4 py-2.5 border-t border-hairline/60 flex items-center gap-2 shrink-0">
            <span v-if="formError" class="text-[11px] text-error truncate max-w-[480px]">{{ formError }}</span>
            <span v-else class="text-[10px] text-on-surface-variant flex items-center gap-1 truncate">
              <span class="material-symbols-outlined text-[13px]">info</span>{{ t('backend.reviewHint') }}
            </span>
            <button class="ml-auto glass-button rounded-lg px-3 py-1 text-[11px]" @click="closeEditor">{{ t('backend.cancel') }}</button>
            <button v-if="canWrite" class="glass-button rounded-lg px-3 py-1 text-[11px] font-semibold flex items-center gap-1"
              :disabled="formBusy" @click="submitEditor">
              <span v-if="formBusy" class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
              {{ t('backend.save') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 审核 -->
    <Teleport to="body">
      <div v-if="verifyOpen" class="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-6">
        <div class="solid-panel rounded-2xl w-[760px] max-h-[84vh] flex flex-col overflow-hidden">
          <div class="panel-bar px-4 py-2.5 flex items-center gap-2 border-b border-hairline/60 shrink-0">
            <span class="material-symbols-outlined text-[16px] text-secondary">fact_check</span>
            <span class="text-[13px] font-semibold">{{ t('backend.verifyTitle') }}</span>
            <span class="text-[11px] text-on-surface-variant">{{ pendingCount }}</span>
            <button v-if="rejectedAudit.length" class="text-[10px] px-1.5 py-0.5 rounded-full border transition-colors ml-1"
              :class="showRejected
                ? 'border-error/40 bg-error/10 text-error'
                : 'border-outline-variant/60 text-on-surface-variant hover:bg-error/5'"
              :title="t('backend.verifyRejectedToggleHint')" @click="showRejected = !showRejected">
              {{ t('backend.verifyRejected') }} {{ rejectedAudit.length }}
              <span class="material-symbols-outlined text-[12px] align-middle">{{ showRejected ? 'expand_less' : 'expand_more' }}</span>
            </button>
            <button class="ml-auto material-symbols-outlined text-[15px] text-on-surface-variant hover:text-secondary"
              :class="verifyBusy ? 'animate-spin' : ''" :title="t('backend.refresh')" :disabled="verifyBusy" @click="loadPending">refresh</button>
            <button class="glass-button rounded-md px-2 py-0.5 text-[11px]" @click="verifyOpen = false">{{ t('backend.close') }}</button>
          </div>
          <div class="flex-1 min-h-0 overflow-y-auto custom-scrollbar relative">
            <div v-for="o in auditRows" :key="o.id" class="px-4 py-2 border-b border-hairline/40 flex items-center gap-2 text-[11px]">
              <span class="font-mono text-graphite shrink-0">#{{ o.id }}</span>
              <span class="truncate text-on-surface min-w-0">{{ o.name }}</span>
              <span class="text-on-surface-variant truncate max-w-[150px] hidden lg:inline">{{ campaignName(o) }}</span>
              <span class="text-on-surface-variant shrink-0">{{ shortDate(o.begin_date) }}</span>
              <span v-if="orderKeywordText(o)" class="text-[10px] px-1.5 py-0.5 rounded-full bg-secondary/10 text-secondary truncate max-w-[130px] shrink-0"
                :title="orderKeywordText(o)">{{ t('backend.verifyKeyword') }}: {{ orderKeywordText(o) }}</span>
              <span v-if="isRejected(o)" class="text-[10px] px-1.5 py-0.5 rounded-full bg-error/10 text-error shrink-0 max-w-[150px] truncate"
                :title="rejectTitle(o)">{{ t('backend.verifyRejected') }}</span>
              <span class="ml-auto flex items-center gap-1 shrink-0">
                <button class="glass-button rounded-md px-2 py-0.5 text-[10px] text-success-indicator" :disabled="verifyBusy"
                  @click="doVerify(o, 'play')">{{ t('backend.verifyPass') }}</button>
                <button v-if="!isRejected(o)" class="glass-button rounded-md px-2 py-0.5 text-[10px] text-error/80" :disabled="verifyBusy"
                  @click="startReject(o)">{{ t('backend.verifyReject') }}</button>
              </span>
            </div>
            <div v-if="!auditRows.length && !verifyBusy" class="py-10 text-center text-[12px] text-on-surface-variant">
              {{ t('backend.verifyEmpty') }}
            </div>
            <div v-if="verifyBusy" class="loading-veil">
              <span class="w-3.5 h-3.5 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
              <span class="text-[11px] text-on-surface-variant">{{ t('backend.loading') }}</span>
            </div>
          </div>
          <div v-if="rejectTarget" class="panel-bar px-4 py-2 border-t border-hairline/60 flex flex-col gap-1.5 shrink-0">
            <div class="text-[11px] text-on-surface">
              {{ t('backend.verifyReason') }} · {{ rejectTarget.name }} (#{{ rejectTarget.id }})
            </div>
            <textarea v-model="rejectMemo" rows="2" class="glass-input px-2 py-1 rounded-md text-[11px] select-text resize-y"
              :placeholder="t('backend.verifyReasonPlaceholder')"></textarea>
            <div class="flex items-center gap-2">
              <button class="glass-button rounded-md px-2.5 py-0.5 text-[11px] text-error/80" :disabled="verifyBusy" @click="doVerify(rejectTarget, 'reject')">
                {{ t('backend.verifyReject') }}
              </button>
              <button class="glass-button rounded-md px-2.5 py-0.5 text-[11px]" @click="rejectTarget = null">{{ t('backend.cancel') }}</button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Custom engine 管理 -->
    <CustomEngineDialog v-model="ceOpen" :seed-value="mac.trim()" @changed="onEngineChanged" />

    <!-- 二次确认 -->
    <Teleport to="body">
      <div v-if="confirmState" class="fixed inset-0 z-[60] bg-black/30 flex items-center justify-center p-6">
        <div class="solid-panel rounded-2xl w-[340px] p-4 flex flex-col gap-3">
          <div class="text-[13px] font-semibold">{{ confirmState.title }}</div>
          <div class="text-[11px] text-on-surface-variant truncate">{{ confirmState.body }}</div>
          <div class="flex justify-end gap-2">
            <button class="glass-button rounded-lg px-3 py-1 text-[11px]" @click="confirmState = null">{{ t('backend.cancel') }}</button>
            <button class="glass-button rounded-lg px-3 py-1 text-[11px]" @click="runConfirmed">{{ t('backend.confirm') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- toast -->
    <Teleport to="body">
      <div v-if="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[70] flex items-center gap-2 pl-3 pr-3.5 py-2 rounded-full solid-panel"
        :class="toastOk ? 'text-secondary' : 'text-error'">
        <span class="material-symbols-outlined text-[15px]">{{ toastOk ? 'check_circle' : 'error' }}</span>
        <span class="text-[11px] max-w-[460px]">{{ toast }}</span>
        <button v-if="toastActionLabel" class="ml-1 px-2.5 py-0.5 rounded-full bg-secondary text-white text-[10px] font-semibold shrink-0"
          @click="runToastAction">{{ toastActionLabel }}</button>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from '@/composables/useI18n'
import SearchSelect from '@/components/SearchSelect.vue'
import LandingInput from '@/components/LandingInput.vue'
import CheckGrid from '@/components/backend/CheckGrid.vue'
import CustomEngineDialog from '@/components/backend/CustomEngineDialog.vue'
import type { SearchSelectOption } from '@/types/searchSelect'
import { MATERIAL_PRESETS, presetsForExt, landingText, type MaterialPreset } from '@/constants/adPresets'
import {
  getOrder,
  listMedias,
  listOrders,
  listPendingOrders,
  listZones,
  materialPreviewUrl,
  parseMaterial,
  searchKeywords,
  listKeywords,
  keywordsByIds,
  invalidateKeywords,
  updateOrderAction,
  updateOrder,
  uploadMaterial,
  verifyOrder,
  listCampaigns,
  listAdvertisers,
  createCampaign,
  loadOrderMeta,
  loadOrderDict,
  materialFieldsOf,
  listOrderApps,
  listOrderZones,
  adTypeLevel1,
  adTypeLevel2,
  adTypeLevel3,
  createOrder,
  type SspAdType,
  type SspAdvertiser,
  type SspCampaign,
  type SspEnv,
  type SspKeyword,
  type SspMedia,
  type SspOrder,
  type SspOrderDict,
  type SspZone,
  type SspAppOption,
} from '@/services/sspApi'

defineOptions({ name: 'AdConfigTab' })

const props = defineProps<{ env: SspEnv; canWrite: boolean }>()
const emit = defineEmits<{
  (e: 'session-expired'): void
  (e: 'logout'): void
  (e: 'switch-env'): void
}>()
const { t, lang } = useI18n()

const envLabel = computed(() => (props.env === 'prod' ? 'PROD' : 'ACC'))

// ── 列表 ───────────────────────────────────────────
const medias = ref<SspMedia[]>([])
const mediaTotal = ref(0)
const mediaBusy = ref(false)
const zones = ref<SspZone[]>([])
const zonesBusy = ref(false)
const orders = ref<SspOrder[]>([])
const selectedMediaId = ref('')
const selectedMedia = computed(() => medias.value.find((m) => m.id === selectedMediaId.value) || null)
const selectedZoneId = ref('')
const adKeyword = ref('')
const page = ref(1)
const pageSize = 50
const total = ref(0)
const ordersBusy = ref(false)

const mediaOptions = computed<SearchSelectOption[]>(() =>
  medias.value.map((m) => ({ value: String(m.id), label: m.name || `#${m.id}`, hint: `#${m.id}` })))

const campaignMap = computed(() => new Map(campaigns.value.map((c) => [String(c.id), c.name])))

function campaignName(o: SspOrder) {
  return o.campaign_name || campaignMap.value.get(String(o.campaign_id)) || o.campaign_id
}

function shortDate(v?: string) {
  return String(v || '').slice(0, 10)
}

async function loadMedias() {
  mediaBusy.value = true
  try {
    const res = await listMedias({ page: 1, pagesize: 300 })
    medias.value = res.records || []
    mediaTotal.value = Math.max(Number(res.total) || 0, medias.value.length)
    const stillThere = medias.value.some((m) => String(m.id) === selectedMediaId.value)
    if (!stillThere) {
      const first = medias.value[0]
      if (first) await selectMedia(String(first.id))
      else {
        selectedMediaId.value = ''
        zones.value = []
        orders.value = []
        total.value = 0
        mediaTotal.value = 0
      }
    }
  } catch (e) {
    handleError(e)
  } finally {
    mediaBusy.value = false
  }
}

function onMediaChange(id: string) {
  selectMedia(id)
}

async function selectMedia(id: string) {
  if (!id) {
    selectedMediaId.value = ''
    selectedZoneId.value = ''
    zones.value = []
    orders.value = []
    total.value = 0
    return
  }
  selectedMediaId.value = id
  selectedZoneId.value = ''
  zones.value = []
  zonesBusy.value = true
  try {
    const res = await listZones(id)
    if (selectedMediaId.value !== id) return
    zones.value = res.records || []
  } catch (e) {
    if (selectedMediaId.value === id) zones.value = []
    handleError(e)
  } finally {
    zonesBusy.value = false
  }
  page.value = 1
  await loadAds()
}

function selectZone(id: string) {
  selectedZoneId.value = id
  page.value = 1
  loadAds()
}

let adsSeq = 0
async function loadAds() {
  macMode.value = false
  appliedKeyword = adKeyword.value.trim()
  const seq = ++adsSeq
  if (!selectedMediaId.value) { orders.value = []; total.value = 0; ordersBusy.value = false; return }
  ordersBusy.value = true
  try {
    const params: Record<string, any> = { page: page.value, pagesize: pageSize, appid: selectedMediaId.value }
    if (adKeyword.value.trim()) params.name = adKeyword.value.trim()
    if (selectedZoneId.value) params.locid = selectedZoneId.value
    const res = await listOrders(params)
    if (seq !== adsSeq) return
    orders.value = res.records
    total.value = res.total
  } catch (e) {
    if (seq === adsSeq) handleError(e)
  } finally {
    if (seq === adsSeq) ordersBusy.value = false
  }
}

function reloadAds() { page.value = 1; loadAds() }

/** 已生效的搜索词，用来判断是否需要重查 */
let appliedKeyword = ''
let searchTimer: ReturnType<typeof setTimeout> | null = null

function applySearch() {
  if (searchTimer) { clearTimeout(searchTimer); searchTimer = null }
  const q = adKeyword.value.trim()
  // MAC 查询结果不受广告名搜索影响，先保持现状
  if (macMode.value) return
  if (q === appliedKeyword) return
  appliedKeyword = q
  reloadAds()
}

/** 输入即搜（防抖 350ms），清空后同样会重新加载，避免停在旧结果上 */
function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => applySearch(), 350)
}

function clearSearch() {
  adKeyword.value = ''
  applySearch()
}

function changePage(delta: number) {
  page.value = Math.max(1, page.value + delta)
  loadAds()
}

/** 写操作后刷新：MAC 结果态下重新按 MAC 查询，避免跳回媒体列表 */
async function refreshList() {
  if (macMode.value) { await doMacQuery(); return }
  await loadAds()
}

// ── MAC 查询 ───────────────────────────────────────
const mac = ref('')
const macBusy = ref(false)
const macMode = ref(false)
const macMatched = ref<SspKeyword[]>([])

async function doMacQuery() {
  const q = mac.value.trim()
  if (!q) { if (macMode.value) clearMac(); return }
  macBusy.value = true
  macMatched.value = []
  try {
    const list = (await searchKeywords(q)) || []
    const lower = q.toLowerCase()
    macMatched.value = list.filter((k) => keywordValue(k).toLowerCase().includes(lower))
    if (!macMatched.value.length) {
      macMode.value = true
      orders.value = []
      total.value = 0
      showToast(t('backend.macRuleNotFound'), false)
      return
    }
    const keys = macMatched.value.slice(0, 5)
    const lists = await Promise.all(keys.map((k) => listOrders({ target_keyword: k.id, page: 1, pagesize: 50 })))
    const map = new Map<string, SspOrder>()
    lists.forEach((r) => (r.records || []).forEach((o) => map.set(String(o.id), o)))
    macMode.value = true
    orders.value = Array.from(map.values())
    total.value = orders.value.length
    if (!orders.value.length) showToast(t('backend.macNoData'), false)
  } catch (e) {
    handleError(e)
  } finally {
    macBusy.value = false
  }
}

/** 清除 MAC 查询结果，恢复到当前媒体/广告位的列表 */
function clearMac() {
  macMode.value = false
  macMatched.value = []
  mac.value = ''
  page.value = 1
  loadAds()
}

// ── 状态：与后台一致（1/3 投放中可暂停，4 已暂停可播放） ──
function canPause(o: SspOrder) {
  const s = String(o.status ?? '')
  return s === '1' || s === '3'
}
function canPlay(o: SspOrder) {
  return String(o.status ?? '') === '4'
}

// ── 通用 ───────────────────────────────────────────
const toast = ref('')
const toastOk = ref(true)
const toastActionLabel = ref('')
let toastAction: (() => void) | null = null
let toastTimer: number | null = null

function showToast(
  text: string,
  ok = true,
  action?: { label: string; run: () => void; duration?: number },
) {
  toast.value = text
  toastOk.value = ok
  toastActionLabel.value = action?.label || ''
  toastAction = action?.run || null
  if (toastTimer) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toast.value = ''
    toastActionLabel.value = ''
    toastAction = null
  }, action?.duration ?? 4000)
}

function runToastAction() {
  const run = toastAction
  toast.value = ''
  toastActionLabel.value = ''
  toastAction = null
  if (toastTimer) window.clearTimeout(toastTimer)
  run?.()
}

function errText(e: unknown) { return e instanceof Error ? e.message : String(e) }

function handleError(e: unknown) {
  const msg = errText(e)
  if (msg.includes('未登录') || msg.toLowerCase().includes('not login')) {
    emit('session-expired')
    return
  }
  showToast(msg, false)
}

const confirmState = ref<{ title: string; body: string; run: () => Promise<void> } | null>(null)
const actionBusyId = ref('')

function askAction(o: SspOrder, action: 'play' | 'pause' | 'delete') {
  const title = action === 'delete' ? t('backend.delete') : action === 'play' ? t('backend.play') : t('backend.pause')
  confirmState.value = {
    title,
    body: `${o.name} (#${o.id})`,
    run: async () => {
      actionBusyId.value = o.id
      try {
        await updateOrderAction(o.id, action)
        showToast(t('backend.updated'), true)
        await refreshList()
      } catch (e) {
        handleError(e)
      } finally {
        actionBusyId.value = ''
      }
    },
  }
}

async function runConfirmed() {
  const state = confirmState.value
  confirmState.value = null
  if (state) await state.run()
}

// ── 广告类型 / 广告主 / Campaign ────────────────────
const adTypes = ref<SspAdType[]>([])
const dict = ref<SspOrderDict>({})
const metaReady = ref(false)
const metaBusy = ref(false)
const metaError = ref('')
const advertisers = ref<SspAdvertiser[]>([])
const advertisersBusy = ref(false)
const campaigns = ref<SspCampaign[]>([])
const campaignsBusy = ref(false)

const campaignOptions = computed<SearchSelectOption[]>(() =>
  campaigns.value.map((c) => ({ value: String(c.id), label: c.name || `#${c.id}`, hint: `#${c.id}` })))
const advertiserOptions = computed<SearchSelectOption[]>(() =>
  advertisers.value.map((a) => ({ value: String(a.id), label: a.name || `#${a.id}`, hint: `#${a.id}` })))

const l1List = computed(() => adTypeLevel1(adTypes.value))
const l2List = computed(() => adTypeLevel2(adTypes.value, editor.adTypeL1))
const l3List = computed(() => adTypeLevel3(adTypes.value, editor.adTypeL1, editor.adTypeL2))

const adTypeUnknown = computed(() =>
  !!editor.adType && !!adTypes.value.length && !adTypes.value.some((x) => x.key === editor.adType))

async function ensureMeta() {
  if (metaReady.value || metaBusy.value) {
    // 已在加载时等它完成
    if (metaBusy.value) {
      while (metaBusy.value) await new Promise((r) => window.setTimeout(r, 60))
    }
    return
  }
  metaBusy.value = true
  metaError.value = ''
  try {
    const meta = await loadOrderMeta()
    adTypes.value = meta.adTypes
    dict.value = meta.dict
    metaReady.value = true
  } catch (e) {
    metaError.value = errText(e)
    handleError(e)
  } finally {
    metaBusy.value = false
  }
}

async function ensureCampaigns() {
  if (campaigns.value.length) return
  campaignsBusy.value = true
  try {
    campaigns.value = await listCampaigns()
  } catch (e) {
    handleError(e)
  } finally {
    campaignsBusy.value = false
  }
}

async function ensureAdvertisers() {
  if (advertisers.value.length) return
  advertisersBusy.value = true
  try {
    advertisers.value = await listAdvertisers()
    if (!editor.advertiserid && advertisers.value.length) editor.advertiserid = String(advertisers.value[0].id)
  } catch (e) {
    handleError(e)
  } finally {
    advertisersBusy.value = false
  }
}

// 后台 Is external=Yes 时的 Ad Formats 字典（优先取页面 dict）
const FALLBACK_AD_FORMATS = ['VAST', 'Google IMA', 'whaletvplus', 'Teads image', 'Teads video', 'VPAID', 'Promo', 'Companion ads']
const adFormatOptions = computed(() => {
  const list = dict.value?.ad_format
  if (Array.isArray(list) && list.length) return list.map((i) => String(i.text || i.id))
  return FALLBACK_AD_FORMATS
})

const priceModeOptions = computed(() => {
  const list = dict.value?.price_mode
  if (Array.isArray(list) && list.length) return list.map((i) => ({ v: String(i.id), t: String(i.text || i.id) }))
  return [{ v: 'CPT', t: 'CPT' }, { v: 'CPM', t: 'CPM' }, { v: 'CPC', t: 'CPC' }]
})

const priorityOptions = computed(() => {
  const list = dict.value?.class
  if (Array.isArray(list) && list.length) return list.map((i) => ({ v: String(i.id), t: String(i.text || i.id) }))
  return [
    { v: '50', t: lang.value === 'en' ? 'Priority over all' : '优先级最高（50）' },
    { v: '100', t: lang.value === 'en' ? 'Priority over external ad' : '高于外部广告（100）' },
    { v: '300', t: lang.value === 'en' ? 'Priority lower than external ad' : '低于外部广告（300）' },
    { v: '400', t: lang.value === 'en' ? 'Priority lower than all' : '优先级最低（400）' },
  ]
})

const FALLBACK_FIELDS = [
  { key: 'image_1', ext: 'mp4,m3u8,jpg,jpeg,png,gif', file_width: 1920, file_height: 1080, file_size: 30000 },
]

function fieldsForType(key: string) {
  const list = materialFieldsOf(adTypes.value.find((x) => x.key === key))
    // 后台的 duration 由系统按默认 15 秒处理，页面不再暴露
    .filter((f) => f.key !== 'duration')
  return list.length ? list : FALLBACK_FIELDS
}

const declaresDuration = computed(() =>
  materialFieldsOf(adTypes.value.find((x) => x.key === editor.adType)).some((f) => f.key === 'duration'))

function fieldMeta(f: any) {
  const bits: string[] = []
  if (f.file_width && f.file_height) bits.push(`${f.file_width}×${f.file_height}`)
  const ext = String(f.ext || '')
  if (ext) bits.push(/^[a-z0-9,]+$/i.test(ext) ? '.' + ext.replace(/,/g, '/') : ext)
  if (f.name) bits.push(String(f.name))
  return bits.join(' · ')
}

function presetsForField(f: any): MaterialPreset[] {
  return presetsForExt(f?.ext)
}

function presetLabel(p: MaterialPreset) {
  const name = lang.value === 'en' ? p.en : p.zh
  return p.note ? `${name} · ${p.note}` : name
}

function todayStr(offset = 0) {
  const d = new Date()
  d.setDate(d.getDate() + offset)
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

/**
 * 结束时间的快捷档位。
 * 平台日历支持 9999-12-31（长期有效），但原生 date 控件翻不到那么远的年份，
 * 这里给一个直接落值的入口，避免用户只能一个月一个月往后点。
 */
const endDatePresets = computed(() => [
  { key: 'd30', label: lang.value === 'en' ? '30d' : '30天', value: todayStr(30), hint: todayStr(30) },
  { key: 'd365', label: lang.value === 'en' ? '1y' : '1年', value: todayStr(365), hint: todayStr(365) },
  {
    key: 'max',
    label: lang.value === 'en' ? 'Max' : '长期',
    value: '9999-12-31',
    hint: t('backend.endDateLongHint'),
  },
])

// ── 编辑器（新建 / 编辑 / 复制） ───────────────────
const editorOpen = ref(false)
const editingId = ref('')
const editingOrder = ref<SspOrder | null>(null)

/** 广告级没有定向规则、但 Campaign 层配了规则时给出说明（这类规则只能在 Campaign 里改） */
const editorCampaignKeyword = computed(() => {
  if (editorKeywords.value.length) return ''
  const cam = String((editingOrder.value as any)?.cam_target_keyword || '').trim()
  return cam ? cam.split(/[;,]/).filter(Boolean).join('; ') : ''
})

/** 平台规则：extend_target=1 表示继承 Campaign，此时广告级 Custom engine 整块不生效 */
const editingInheritCampaign = computed(
  () => String((editingOrder.value as any)?.extend_target ?? '') === '1',
)
const editor = reactive({
  campaignMode: 'existing' as 'existing' | 'new',
  campaignId: '',
  campaignName: '',
  advertiserid: '',
  demandPartner: '',
  name: '',
  adType: 'Screensaver',
  adTypeL1: '',
  adTypeL2: '',
  adTypeL3: '',
  clickUrl: '',
  beginDate: '',
  endDate: '',
  priceMode: 'CPT',
  adClass: '50',
  disableAdflag: '1',
  external: '0',
  adFormat: '',
  material: {} as Record<string, string>,
})
const editorAppIds = ref<string[]>([])
const editorZoneIds = ref<string[]>([])
const editorApps = ref<SspAppOption[]>([])
const editorZones = ref<SspZone[]>([])
const editorAppsBusy = ref(false)
const editorZonesBusy = ref(false)
const editorKeywords = ref<SspKeyword[]>([])
const editorPreview = ref<Record<string, string>>({})
const editorUploading = ref('')
/** 后台素材里的视频时长：界面不展示，但编辑时要保留原值 */
const editorDuration = ref('')
const editorInputs = new Map<string, HTMLInputElement | null>()
const formBusy = ref(false)
const formError = ref('')

const editorFields = computed(() => fieldsForType(editor.adType))

const selectedAdTypeHint = computed(() => {
  const f = editorFields.value[0] as any
  if (!f) return ''
  const size = f.file_width && f.file_height ? `${f.file_width}×${f.file_height}` : ''
  const ext = f.ext ? String(f.ext).replace(/,/g, ' / ').toUpperCase() : ''
  const max = f.file_size ? `${Math.round(Number(f.file_size) / 1024 * 10) / 10}MB` : ''
  return [size, ext, max].filter(Boolean).join(' · ')
})

// —— 三级广告类型 ——
function setAdTypeChain(key: string) {
  const found = adTypes.value.find((x) => x.key === key)
  if (found) {
    editor.adTypeL1 = String(found.text ?? '')
    editor.adTypeL2 = String(found.sub_text ?? '')
    editor.adTypeL3 = found.key
    return
  }
  // 未知类型：三级下拉先落到第一项，保留原 adType 不做覆盖
  const l1 = adTypeLevel1(adTypes.value)[0]
  editor.adTypeL1 = l1?.value ?? ''
  editor.adTypeL2 = adTypeLevel2(adTypes.value, editor.adTypeL1)[0]?.value ?? ''
  editor.adTypeL3 = adTypeLevel3(adTypes.value, editor.adTypeL1, editor.adTypeL2)[0]?.value ?? ''
}

function applyAdType(key: string) {
  if (!key) return
  const changed = editor.adType !== key
  editor.adType = key
  if (changed) {
    editor.material = {}
    editorPreview.value = {}
  }
  void reloadEditorApps()
}

function onL1Change(v: string) {
  editor.adTypeL1 = v
  editor.adTypeL2 = adTypeLevel2(adTypes.value, v)[0]?.value ?? ''
  const next = adTypeLevel3(adTypes.value, v, editor.adTypeL2)[0]?.value ?? ''
  editor.adTypeL3 = next
  applyAdType(next)
}

function onL2Change(v: string) {
  editor.adTypeL2 = v
  const next = adTypeLevel3(adTypes.value, editor.adTypeL1, v)[0]?.value ?? ''
  editor.adTypeL3 = next
  applyAdType(next)
}

function onL3Change(v: string) {
  editor.adTypeL3 = v
  applyAdType(v)
}

// —— Assigned media / zone：与后台 selectapps / selectlocs 联动 ——
let appsSeq = 0
let zonesSeq = 0
/** 新建广告时广告位是否已做过「默认全选」 */
const zoneDefaulted = ref(false)

async function reloadEditorApps() {
  const seq = ++appsSeq
  editorAppsBusy.value = true
  try {
    const list = await listOrderApps(editor.campaignId, editor.adType)
    if (seq !== appsSeq) return
    editorApps.value = list
    const valid = new Set(list.map((a) => a.id))
    const kept = editorAppIds.value.filter((id) => valid.has(id))
    if (kept.length !== editorAppIds.value.length) {
      const dropped = editorAppIds.value.length - kept.length
      editorAppIds.value = kept
      // 平台的可选媒体范围随广告类型变化，被剔除的媒体要告知，避免以为参数丢了
      if (editingId.value) showToast(t('backend.mediaFiltered', { n: String(dropped) }), false)
    }
    // 新建时给一个默认媒体（当前左栏选中的），编辑时绝不擅自改动原有定向
    if (!editorAppIds.value.length && !editingId.value) {
      const prefer = selectedMediaId.value
      if (prefer && valid.has(prefer)) editorAppIds.value = [prefer]
      else if (valid.size === 1) editorAppIds.value = Array.from(valid)
    }
  } catch (e) {
    if (seq === appsSeq) handleError(e)
  } finally {
    if (seq === appsSeq) editorAppsBusy.value = false
  }
  if (seq === appsSeq) await reloadEditorZones()
}

async function reloadEditorZones() {
  const seq = ++zonesSeq
  if (!editorAppIds.value.length || !editor.adType) {
    editorZones.value = []
    editorZoneIds.value = []
    editorZonesBusy.value = false
    return
  }
  editorZonesBusy.value = true
  try {
    const list = await listOrderZones(editor.adType, editorAppIds.value)
    if (seq !== zonesSeq) return
    editorZones.value = list
    const valid = new Set(list.map((z) => z.id))
    const kept = editorZoneIds.value.filter((id) => valid.has(id))
    if (kept.length !== editorZoneIds.value.length) editorZoneIds.value = kept
    // 新建广告首次拿到广告位时默认全选，之后交给用户自己控制
    if (!editingId.value && !zoneDefaulted.value && !editorZoneIds.value.length && list.length) {
      editorZoneIds.value = list.map((z) => z.id)
      zoneDefaulted.value = true
    }
  } catch (e) {
    if (seq === zonesSeq) handleError(e)
  } finally {
    if (seq === zonesSeq) editorZonesBusy.value = false
  }
}

function onAppsChange(v: string[]) {
  editorAppIds.value = v
  // 广告位选项随媒体变化；仍然有效的已选广告位保留（与后台一致）
  void reloadEditorZones()
}

function onZonesChange(v: string[]) {
  editorZoneIds.value = v
}

function onCampaignChange(v: string) {
  editor.campaignId = v
  void reloadEditorApps()
}

function setEditorInput(key: string, el: any) { editorInputs.set(key, el as HTMLInputElement | null) }
function pickEditorFile(key: string) { editorInputs.get(key)?.click() }

async function uploadEditorField(key: string, ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  editorUploading.value = key
  try {
    const res = await uploadMaterial(file, '3')
    editor.material[key] = res.file_id
    editorPreview.value[key] = materialPreviewUrl(props.env, res.file_path)
  } catch (e) {
    handleError(e)
  } finally {
    editorUploading.value = ''
  }
}

function applyPreset(key: string, ev: Event) {
  const el = ev.target as HTMLSelectElement
  const id = el.value
  el.value = ''
  if (!id) return
  const preset = MATERIAL_PRESETS.find((p) => p.id === id)
  if (!preset) return
  editor.material[key] = preset.url
  editorPreview.value[key] = preset.url
  showToast(`${t('backend.presetApplied')}: ${presetLabel(preset)}`, true)
}

function resetEditor() {
  formError.value = ''
  editor.campaignMode = 'existing'
  editor.campaignId = ''
  editor.campaignName = ''
  editor.demandPartner = ''
  editor.name = ''
  editor.adType = ''
  editor.adTypeL1 = ''
  editor.adTypeL2 = ''
  editor.adTypeL3 = ''
  editor.clickUrl = ''
  editor.beginDate = todayStr()
  editor.endDate = todayStr(30)
  editor.priceMode = 'CPT'
  editor.adClass = '50'
  editor.disableAdflag = '1'
  editor.external = '0'
  editor.adFormat = ''
  editor.material = {}
  editorPreview.value = {}
  editorAppIds.value = []
  editorZoneIds.value = []
  editorApps.value = []
  editorZones.value = []
  editorKeywords.value = []
  keywordQuery.value = ''
  keywordResults.value = []
  editorDuration.value = ''
  zoneDefaulted.value = false
}

async function openNewAd() {
  editingId.value = ''
  editingOrder.value = null
  resetEditor()
  editorOpen.value = true
  editorAppsBusy.value = true
  editorZonesBusy.value = true
  await ensureMeta()
  if (adTypes.value.length) {
    const first = adTypes.value.find((x) => x.key === 'Screensaver') || adTypes.value[0]
    editor.adType = first?.key ?? ''
    setAdTypeChain(editor.adType)
  }
  void ensureCampaigns()
  void ensureAdvertisers()
  await reloadEditorApps()
}

async function openEdit(o: SspOrder) {
  formError.value = ''
  editingId.value = String(o.id)
  resetEditor()
  editorOpen.value = true
  editorAppsBusy.value = true
  editorZonesBusy.value = true
  void ensureCampaigns()
  void ensureAdvertisers()
  await ensureMeta()
  try {
    const fresh = (await getOrder(o.id)) || o
    editingOrder.value = fresh
    const mat = parseMaterial(fresh)
    const nextMat: Record<string, string> = {}
    Object.keys(mat).forEach((k) => {
      const v = mat[k]
      if (k === 'ad_format' || k === 'duration') return
      nextMat[k] = v && typeof v === 'object' ? JSON.stringify(v) : String(v ?? '')
    })
    editor.campaignMode = 'existing'
    editor.campaignId = String(fresh.campaign_id || '')
    editor.name = String(fresh.name || '')
    editor.adType = String(fresh.ad_type || '')
    setAdTypeChain(editor.adType)
    // click_url 可能是字符串 / 对象 / 数组，取第一条非空的原文；详情里没有时回落到列表行
    editor.clickUrl = [fresh.click_url, (fresh as any).clickurl, (o as any)?.click_url]
      .map((v) => landingText(v))
      .find((v) => v) || ''
    editor.beginDate = shortDate(fresh.begin_date) || todayStr()
    editor.endDate = shortDate(fresh.end_date) || todayStr(30)
    editor.priceMode = String(fresh.price_mode || 'CPT')
    editor.adClass = String(fresh.class || '50')
    editor.disableAdflag = String(fresh.disable_adflag ?? '1')
    editor.external = String(fresh.external ?? '0')
    editor.adFormat = String(mat.ad_format || '')
    editorDuration.value = mat.duration !== undefined ? String(mat.duration) : ''
    editor.material = nextMat
    const apps = String(fresh.target_app || '').split(/[;,]/).map((s) => s.trim()).filter(Boolean)
    editorAppIds.value = apps
    const locs = String(fresh.locids || '').split(/[;,]/).map((s) => s.trim()).filter(Boolean)
    editorZoneIds.value = locs
    // 定向规则（Custom engine）
    const rawKid = (fresh as any).target_keyword
    const kid = Array.isArray(rawKid) ? rawKid.join(';') : String(rawKid ?? '').trim()
    const ids = kid ? kid.split(/[;,]/).map((s) => s.trim()).filter((s) => s && s !== '0') : []
    editorKeywords.value = await restoreKeywords(ids, fresh)
  } catch (e) {
    handleError(e)
  }
  await reloadEditorApps()
}

function closeEditor() {
  editorOpen.value = false
  editingId.value = ''
  editingOrder.value = null
}

const copyBusyId = ref('')

async function copyOrder(o: SspOrder) {
  copyBusyId.value = o.id
  try {
    await openEdit(o)
    editingId.value = ''
    editingOrder.value = null
    editor.name = `${o.name || ''} COPY`
    editor.beginDate = todayStr()
    showToast(t('backend.copyReady'), true)
  } catch (e) {
    handleError(e)
  } finally {
    copyBusyId.value = ''
  }
}

function notifyNeedVerify(created: boolean) {
  // 平台规则：新建 / 修改广告都要到「审核」里通过后才会生效，必须明确告诉用户
  showToast(
    created ? t('backend.createdNeedVerify') : t('backend.savedNeedVerify'),
    true,
    { label: t('backend.goVerify'), run: () => openVerify(), duration: 9000 },
  )
}

async function submitEditor() {
  formError.value = ''
  if (!editor.name.trim()) { formError.value = t('backend.adName') + ' ' + t('backend.required'); return }
  if (!editor.adType) { formError.value = t('backend.selectAdType'); return }
  if (!editorAppIds.value.length) { formError.value = t('backend.mediaRequired'); return }
  if (!editorZoneIds.value.length) { formError.value = t('backend.zoneRequired'); return }
  if (!editingId.value && editor.campaignMode === 'existing' && !editor.campaignId) {
    formError.value = t('backend.selectCampaign'); return
  }
  if (!editingId.value && editor.campaignMode === 'new' && (!editor.campaignName.trim() || !editor.demandPartner.trim() || !editor.advertiserid)) {
    formError.value = t('backend.campaignName') + ' / ' + t('backend.demandPartner') + ' ' + t('backend.required'); return
  }
  formBusy.value = true
  try {
    const material = { ...editor.material } as Record<string, any>
    delete material.duration
    // 视频类广告需要时长：界面不展示，保留原值或按平台默认 15 秒补齐
    if (declaresDuration.value) material.duration = Number(editorDuration.value) || 15
    if (editor.external === '1' && editor.adFormat) material.ad_format = editor.adFormat

    // 定向规则按平台的数组形式提交；空数组用 [''] 显式清空（否则后端会保留旧值）
    const keywordList = editorKeywords.value.map((k) => String(k.id)).filter(Boolean)
    const keywordIds = keywordList.length ? keywordList : ['']

    if (editingId.value && editingOrder.value) {
      await updateOrder(editingOrder.value, {
        name: editor.name.trim(),
        campaign_id: editor.campaignId || editingOrder.value.campaign_id,
        ad_type: editor.adType,
        click_url: editor.clickUrl.trim(),
        begin_date: `${editor.beginDate} 00:00:00`,
        end_date: `${editor.endDate} 23:59:59`,
        price_mode: editor.priceMode,
        class: editor.adClass,
        disable_adflag: editor.disableAdflag,
        external: editor.external,
        target_app: editorAppIds.value.join(';'),
        locids: editorZoneIds.value.join(';'),
        target_keyword: keywordIds,
        // 配了广告级 Custom engine 就必须是「自定义定向」，
        // 否则（继承 Campaign）平台会整块忽略广告级定向，指定 MAC 不生效
        extend_target: keywordList.length ? '0' : String((editingOrder.value as any).extend_target ?? '0'),
        material,
      })
      notifyNeedVerify(false)
    } else {
      let campaignId = editor.campaignId
      if (editor.campaignMode === 'new') {
        campaignId = await createCampaign({
          name: editor.campaignName.trim(),
          advertiserid: String(editor.advertiserid),
          demandPartner: editor.demandPartner.trim(),
          beginDate: `${editor.beginDate} 00:00:00`,
          endDate: `${editor.endDate} 23:59:59`,
        })
        campaigns.value = []
      }
      await createOrder({
        campaignId,
        name: editor.name.trim(),
        adType: editor.adType,
        material,
        clickUrl: editor.clickUrl.trim(),
        appIds: editorAppIds.value,
        locIds: editorZoneIds.value,
        beginDate: `${editor.beginDate} 00:00:00`,
        endDate: `${editor.endDate} 23:59:59`,
        keywordId: keywordIds,
        priceMode: editor.priceMode,
        adClass: editor.adClass,
        disableAdflag: editor.disableAdflag,
        external: editor.external,
        adFormat: editor.adFormat,
      })
      notifyNeedVerify(true)
    }
    closeEditor()
    await loadAds()
  } catch (e) {
    handleError(e)
  } finally {
    formBusy.value = false
  }
}

// ── Custom engine（指定 MAC） ──────────────────────
const keywordQuery = ref('')
const keywordResults = ref<SspKeyword[]>([])
const keywordBusy = ref(false)
const ceOpen = ref(false)

function keywordValue(k: SspKeyword) {
  const vc = k.valuecode
  if (Array.isArray(vc)) return vc.join(';')
  return String(vc || '')
}

function keywordLabel(k: SspKeyword) {
  return String(k.valuetext || k.keytext || keywordValue(k) || `#${k.id}`)
}

/**
 * 编辑回显定向规则：
 * 1. 先用 id 在全量规则里匹配；匹配不到时强制绕过缓存再查一次（新建规则 / 切环境后缓存会旧）；
 * 2. 仍然匹配不到（规则被删、跨环境）就用平台返回的 target_keyword_text 兜底显示，
 *    实在没有文字则显示 #id —— 保证不会「看起来没配置」，保存时 id 也不会丢。
 */
async function restoreKeywords(ids: string[], order: SspOrder): Promise<SspKeyword[]> {
  if (!ids.length) return []
  let list: SspKeyword[] = []
  try {
    list = await keywordsByIds(ids)
  } catch {
    list = []
  }
  const map = new Map(list.map((k) => [String(k.id), k]))
  if (ids.some((id) => !map.has(String(id)))) {
    const texts = (order as any).target_keyword_text
    const names: string[] = Array.isArray(texts)
      ? texts.map((x: any) => String(x))
      : String(texts || '').split(/[;,]/).filter(Boolean)
    return ids.map((id, i) => {
      const hit = map.get(String(id))
      if (hit) return hit
      const label = names[i] || ''
      return {
        id,
        keycode: '',
        keytext: label,
        valuetext: label || `#${id}`,
        valuecode: '',
        unresolved: true,
      } as SspKeyword
    })
  }
  return ids.map((id) => map.get(String(id)) as SspKeyword)
}

function engineTitle(k: SspKeyword) {
  const name = keywordLabel(k)
  const val = keywordValue(k)
  return val && val !== name ? `${name} · ${val}` : name
}

/** 规则在当前环境里查不到（被删 / 跨环境）时的占位标记 */
function isUnresolved(k: SspKeyword) {
  return Boolean((k as any).unresolved)
}

async function doKeywordSearch() {
  const q = keywordQuery.value.trim()
  if (!q) return
  keywordBusy.value = true
  try {
    const res = await listKeywords(q.includes(':') ? { value: q, pagesize: 30 } : { name: q, pagesize: 30 })
    const picked = new Set(editorKeywords.value.map((k) => String(k.id)))
    keywordResults.value = res.records.filter((k) => !picked.has(String(k.id)))
    if (!keywordResults.value.length) showToast(t('backend.engineNoMatch'), false)
  } catch (e) {
    handleError(e)
  } finally {
    keywordBusy.value = false
  }
}

function pickKeyword(k: SspKeyword) {
  if (!editorKeywords.value.some((x) => String(x.id) === String(k.id))) {
    editorKeywords.value = [...editorKeywords.value, k]
  }
  keywordResults.value = []
  keywordQuery.value = ''
}

function removeKeyword(id: string) {
  editorKeywords.value = editorKeywords.value.filter((k) => String(k.id) !== String(id))
}

function openEngineDialog() {
  ceOpen.value = true
}

async function onEngineChanged() {
  // 规则被改 / 删后，已选规则的文字需要重新对齐
  invalidateKeywords()
  const ids = editorKeywords.value.map((k) => String(k.id))
  if (!ids.length) return
  try {
    editorKeywords.value = await keywordsByIds(ids)
  } catch {
    // 忽略
  }
}

// ── 审核 ───────────────────────────────────────────
const verifyOpen = ref(false)
const verifyBusy = ref(false)
const pendingOrders = ref<SspOrder[]>([])
const pendingTotal = ref(0)
const rejectTarget = ref<SspOrder | null>(null)
const rejectMemo = ref('')
/** 平台「Ad verify」列表会把已拒绝的广告一起返回（status=2），默认收起来只显示真正的待审核 */
const showRejected = ref(false)

function isRejected(o: SspOrder) {
  return String(o.status) === '2'
}
function rejectTitle(o: SspOrder) {
  const r = String((o as any).verify_reason || '').trim()
  return `${t('backend.verifyRejected')}: ${r || '-'}`
}
const pendingAudit = computed(() => pendingOrders.value.filter((o) => String(o.status) === '0'))
const rejectedAudit = computed(() => pendingOrders.value.filter(isRejected))
const pendingCount = computed(() => pendingAudit.value.length)
const auditRows = computed(() => (showRejected.value ? pendingOrders.value : pendingAudit.value))

/** 待审核列表里展示该广告自己的定向规则（规则被删 / 环境不同时后端只给文字） */
function orderKeywordText(o: SspOrder) {
  const raw = (o as any).target_keyword_text
  const arr: string[] = Array.isArray(raw) ? raw.map((x: any) => String(x)) : String(raw || '').split(/[;,]/).filter(Boolean)
  return arr.join(' · ')
}

function openVerify() {
  verifyOpen.value = true
  rejectTarget.value = null
  showRejected.value = false
  loadPending()
}

async function loadPending() {
  verifyBusy.value = true
  try {
    const res = await listPendingOrders({ page: 1, pagesize: 100 })
    pendingOrders.value = res.records || []
    pendingTotal.value = Number(res.total) || pendingOrders.value.length
  } catch (e) {
    handleError(e)
  } finally {
    verifyBusy.value = false
  }
}

function startReject(o: SspOrder) {
  rejectTarget.value = o
  rejectMemo.value = ''
}

async function doVerify(o: SspOrder, action: 'play' | 'reject') {
  verifyBusy.value = true
  try {
    const memo = action === 'reject' ? rejectMemo.value : ''
    await verifyOrder(o.id, action, memo)
    rejectTarget.value = null
    if (action === 'play') {
      // 通过后再读一次，确认审核动作没有把定向规则吞掉（改 MAC 后走审核 = 常见场景）
      const fresh = await getOrder(o.id).catch(() => null)
      const before = String((o as any).target_keyword || '').trim()
      const after = String((fresh as any)?.target_keyword || '').trim()
      if (fresh && before && !after) showToast(t('backend.verifyKeywordLost'), false)
      else showToast(t('backend.updated'), true)
    } else {
      // 平台拒绝后广告仍留在审核列表（status=2 Rejected，状态列显示「已拒绝」），
      // 不是接口没生效；这里就地把它标成已拒绝，主列表立刻移出，需要放行时可展开「已拒绝」
      ;(o as any).status = '2'
      ;(o as any).verify_reason = memo
      showToast(t('backend.verifyRejectedToast'), true)
    }
    await loadPending()
    await refreshList()
  } catch (e) {
    handleError(e)
  } finally {
    verifyBusy.value = false
  }
}

onMounted(() => {
  loadMedias()
  ensureCampaigns().catch(() => {})
  loadOrderDict().then((d) => { dict.value = d }).catch(() => {})
  // 打开页面时就拿到待审核数量，审核入口能直接显示待办
  loadPending().catch(() => {})
})
</script>
