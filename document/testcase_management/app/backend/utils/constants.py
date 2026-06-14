"""
Zmind PR 状态相关常量

关闭状态：被视为"已关闭"的 PR 状态，不计入未关闭统计
开放状态：被视为"进行中/未关闭"的 PR 状态，用于排序（开放排前面）
"""
CLOSED_STATUSES = {'Closed', 'Suspended', 'Pending', 'Device Issue', 'App Issue'}

OPEN_STATUS_ORDER = ['New', 'On-going', 'Re-Open', 'Verification Failed', 'Info', 'Confirm']
