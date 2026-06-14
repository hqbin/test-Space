const initSqlJs = require('sql.js')
const fs = require('fs')
const path = require('path')

function genId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

const modules = ['登录模块', '注册模块', '支付模块', '用户中心', '商品详情', '购物车', '订单管理', '消息通知', '搜索功能', '客服系统']
const titles = [
  '输入正确用户名密码登录成功',
  '输入错误密码登录失败提示',
  '空用户名登录提示',
  '空密码登录提示',
  '密码长度不足6位提示',
  '连续5次登录失败锁定账号',
  '记住密码功能验证',
  '忘记密码重置流程',
  '多设备登录踢出逻辑',
  '登录态过期自动刷新',
]
const stepsList = [
  '1. 打开登录页面\n2. 输入用户名\n3. 输入密码\n4. 点击登录按钮\n5. 验证跳转',
  '1. 打开登录页面\n2. 输入错误凭证\n3. 点击登录\n4. 验证错误提示',
  '1. 打开页面\n2. 清空输入框\n3. 直接点击提交\n4. 验证表单校验',
]
const expectedList = [
  '登录成功，跳转到首页',
  '显示错误提示信息',
  '页面给出必填项校验提示',
  '系统正常处理无崩溃',
  '数据保存成功，页面刷新后一致',
  '操作完成后页面状态正确',
]

const cases = []
for (let i = 0; i < 199; i++) {
  const mod = modules[i % modules.length]
  const ti = titles[i % titles.length]
  cases.push({
    id: genId(),
    module: mod,
    title: `${ti} #${i + 1}`,
    precondition: i % 3 === 0 ? '用户已登录系统' : '用户未登录',
    steps: stepsList[i % stepsList.length],
    expected: expectedList[i % expectedList.length],
    priority: ['P0', 'P1', 'P2', 'P3'][i % 4],
    tags: i % 5 === 0 ? ['冒烟', '回归'] : i % 3 === 0 ? ['边界'] : [],
    assignee: ['张三', '李四', '王五'][i % 3],
    remarks: i % 7 === 0 ? '重点关注' : '',
  })
}

const fileId = genId()
const now = new Date().toISOString()

const caseFile = {
  id: fileId,
  name: '全量回归测试用例集',
  version: '1.0',
  cases,
  createdAt: now,
  updatedAt: now,
  tags: ['回归', '全量'],
  customFields: [],
}

const dbDir = path.join(process.env.APPDATA, 'com.testspace.app')
if (!fs.existsSync(dbDir)) fs.mkdirSync(dbDir, { recursive: true })
const dbPath = path.join(dbDir, 'test-space.db')

async function seed() {
  const SQL = await initSqlJs()
  let buffer
  try { buffer = fs.readFileSync(dbPath) } catch { buffer = null }
  const db = new SQL.Database(buffer)

  db.run(`CREATE TABLE IF NOT EXISTS field_rule_sets (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, rules TEXT NOT NULL,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
  )`)
  db.run(`CREATE TABLE IF NOT EXISTS case_files (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, data TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]', custom_fields TEXT NOT NULL DEFAULT '[]',
    rule_set_id TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
  )`)
  db.run(`CREATE TABLE IF NOT EXISTS recent_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL, case_count INTEGER NOT NULL DEFAULT 0, last_opened TEXT NOT NULL
  )`)
  db.run(`CREATE TABLE IF NOT EXISTS favorites (
    path TEXT PRIMARY KEY, added_at TEXT NOT NULL
  )`)
  db.run(`CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY, value TEXT NOT NULL
  )`)

  db.run(
    `INSERT OR REPLACE INTO case_files (id, name, data, tags, custom_fields, rule_set_id, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
    [fileId, caseFile.name, JSON.stringify(caseFile), JSON.stringify(caseFile.tags), JSON.stringify(caseFile.customFields), '', now, now]
  )

  db.run(
    `INSERT OR REPLACE INTO recent_files (path, name, case_count, last_opened)
     VALUES (?, ?, ?, ?)`,
    [`db://${fileId}`, caseFile.name, cases.length, now]
  )

  const data = db.export()
  fs.writeFileSync(dbPath, Buffer.from(data))
  db.close()
  console.log(`Seeded ${cases.length} cases to ${dbPath}`)
  console.log(`File: "${caseFile.name}" (ID: ${fileId})`)
  console.log(`Modules: ${[...new Set(cases.map(c => c.module))].join(', ')}`)
  console.log(`Priorities: ${[...new Set(cases.map(c => c.priority))].join(', ')}`)
}

seed().catch(e => { console.error(e); process.exit(1) })
