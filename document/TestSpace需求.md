# Test Space 系统设计文档 V1.0

# 一、项目概述

## 产品名称

Test Space

## 产品定位

Test Space 是一款面向软件测试工程师的 Windows 桌面工作台。

目标：

统一测试工程师日常工作入口。

将：

* 测试用例设计
* 测试平台管理
* ADB调试
* 串口调试
* 日志分析
* 脚本执行
* 知识沉淀

整合到一个桌面应用中。

产品定位：

Cursor for Testing

而非传统测试管理平台。

现有测试平台继续承担：

* 数据存储
* 权限管理
* 业务管理

Test Space 作为桌面客户端和效率工具。

---

# 二、技术架构

## 桌面框架

Tauri 2

## 前端

Vue 3

TypeScript

Vite

Pinia

Vue Router

TailwindCSS

shadcn-vue

## 编辑器

Monaco Editor

TipTap

## 思维导图

LogicFlow

或

AntV X6

## 表格

TanStack Table

## 图表

ECharts

## 动画

Motion Vue

## 原生层

Rust

负责：

ADB

串口

脚本执行

文件系统

系统能力

---

# 三、整体设计原则

## 设计理念

Apple Human Interface

Cursor

Arc Browser

Notion

Obsidian

---

## 产品特征

轻量

现代

高级

沉浸

高效率

AI增强

---

## 设计要求

浅色主题优先

液态玻璃风格

毛玻璃材质

大留白

高层级感

低信息噪音

避免后台管理系统风格

避免传统企业软件风格

---

# 四、导航结构

Workspace

Case Space

Device Space

Notes Space

Platform Space

Script Space

Settings

AI不作为独立菜单

AI能力嵌入各模块

---

# 五、Workspace

## 功能定位

首页

工作台

最近工作入口

---

## 页面内容

欢迎区域

最近编辑用例

最近编辑笔记

最近连接设备

最近运行脚本

最近同步记录

---

## 快捷操作

新建用例

连接设备

打开笔记

执行脚本

打开平台

---

## Command Center

页面中心提供统一输入入口

支持：

生成测试用例

分析日志

生成SQL

生成测试报告

搜索内容

跳转页面

---

# 六、Case Space

## 功能定位

测试用例设计中心

核心模块

---

## 数据来源

可以来自平台接口

可以保存Excel和思维导图到本地

可以用例可以同步到平台

---

## 支持视图

---

### Excel View

表格视图
默认视图


---

### Mind Map View

思维导图

---

## 数据模型

统一数据结构

所有视图基于同一份数据渲染

禁止互相转换

统一状态管理

---

## 用例字段

模块
用例标题
前置条件
操作步骤
预期结果
用例等级
备注
扩展字段

---

## 自定义字段

动态生成字段

支持新增

支持修改

支持隐藏

---

## AI生成用例

输入支持：

需求文档

PRD

产品说明

截图

网页链接

文本描述

---

输出支持：

测试点

测试计划

测试用例

思维导图

边界场景

异常场景

---

## 平台同步

获取平台用例

编辑

保存

提交

版本管理

冲突检测

---

# 七、Device Space

## 功能定位

设备管理中心

ADB中心

串口中心

日志中心

---

## 设备列表

设备名称

Android版本

固件版本

IP地址

在线状态

CPU占用

内存占用

---

## ADB模块

支持：

设备列表

ADB Shell

安装APK

卸载APK

Push

Pull

重启

截图

录屏

Logcat

---

## 串口模块

支持：

连接串口

断开串口

发送命令

命令收藏

自动发送

日志保存

日志导出

---

## 日志中心

支持：

Logcat

Kernel

Serial

Application

---

## AI日志分析

支持：

Crash分析

ANR分析

异常分析

风险分析

根因定位

修复建议

---

# 八、Notes Space

## 功能定位

知识管理中心

测试经验沉淀中心

---

## 编辑器

Markdown

---

## 支持内容

文本

代码

图片

附件

表格

Mermaid

---

## 功能

标签

双向链接

全文搜索

历史版本

收藏

分类

---

## 关联能力

关联测试用例

关联设备

关联日志

关联版本

---

## 数据存储

通过平台接口保存

可以选择保存到本地文件

---

# 九、Script Space

## 功能定位

脚本管理与执行中心

---

## 支持类型

Python

BAT

CMD

PowerShell

---

## 功能

脚本库

脚本分类

脚本搜索

脚本收藏

执行历史

运行日志

参数配置

---

## 执行能力

Rust启动进程

实时输出日志

支持终止

支持重试

支持导出

---

## 设备关联

支持选择设备执行

支持ADB场景脚本

---

# 十、Platform Space（这部分都是平台已有的部分功能移植桌面端）

## 功能定位

现有测试平台桌面客户端

---
## 版本发布管理

版本列表

版本编辑

发布记录

更新说明

审核记录

---

## 用户行为分析

埋点统计

活跃用户

功能分析

使用趋势

---


## 数据库管理

---

## 所属模块

Platform Space

子功能

---

## 功能

数据源管理

连接管理

SQL编辑器

执行SQL

结果查看

历史记录

SQL收藏

SQL模板

导出结果

---

## AI能力

自然语言生成SQL

SQL解释

SQL优化建议

---

## 安全机制

危险SQL识别

DELETE确认

UPDATE确认

TRUNCATE确认

执行审计

操作日志

---

# 十二、AI能力体系

## 设计原则

AI不作为独立页面

AI融入所有模块

---

## Case Space

生成测试点

生成测试计划

生成测试用例

生成思维导图

---

## Device Space

日志分析

Crash分析

ANR分析

根因定位

---

## Notes Space

笔记总结

内容润色

知识提炼

---

## Script Space

生成脚本

优化脚本

解释脚本

---

## Database

生成SQL

优化SQL

解释SQL

---

## 全局能力

Ctrl + K

打开 Command Center

统一AI入口

---

# 十三、接口设计原则

## 数据来源

全部来源于平台后端接口

---

## 本地存储

仅保存：

用户配置

窗口状态

主题配置

最近打开记录

缓存文件

---

## 业务数据

全部通过接口获取

全部通过接口保存

不建立本地业务数据库

---

# 十四、权限体系

Admin

Leader

Tester

Guest

权限由平台统一管理

客户端只负责展示

---

# 十五、开发阶段

## Phase 1

Workspace

Case Space

Device Space

ADB

串口

平台登录

平台同步

---

## Phase 2

Notes Space

Script Space

数据库管理

AI日志分析

---

## Phase 3

版本发布

埋点分析

插件系统

自动化测试集成

Agent能力

---

# 十六、最终目标

打造一款：

面向软件测试工程师的

Apple级体验

Cursor级效率

统一测试工作入口

让测试工程师每天打开的第一个工具就是 Test Space。
