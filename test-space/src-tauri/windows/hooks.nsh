; NSIS 安装程序钩子
; 在安装前删除所有位置的旧快捷方式，防止桌面快捷方式重复

!macro NSIS_HOOK_PREINSTALL
  ; 删除当前用户的桌面快捷方式
  Delete "$DESKTOP\${PRODUCTNAME}.lnk"
  ; 删除当前用户的开始菜单快捷方式（无 startMenuFolder 时直接在 $SMPROGRAMS 根目录）
  Delete "$SMPROGRAMS\${PRODUCTNAME}.lnk"

  ; 删除所有用户的桌面和开始菜单快捷方式
  ; （解决用户切换安装模式 perUser/perMachine 后产生重复快捷方式的问题）
  SetShellVarContext all
  Delete "$DESKTOP\${PRODUCTNAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCTNAME}.lnk"
  SetShellVarContext current
!macroend

!macro NSIS_HOOK_POSTINSTALL
  ; 先通知 exe 本身图标已变更，失效 Shell 对该 exe 的图标缓存条目
  ; SHCNE_UPDATEITEM=0x2000, SHCNF_PATHW|SHCNF_FLUSH=0x1005
  System::Call "shell32::SHChangeNotify(i 0x2000, i 0x1005, t '$INSTDIR\${PRODUCTNAME}.exe', i 0)"

  ; 再通知桌面快捷方式变更，Shell 会重新解析 .lnk → 重新从 exe 读取图标
  System::Call "shell32::SHChangeNotify(i 0x2000, i 0x1005, t '$DESKTOP\${PRODUCTNAME}.lnk', i 0)"

  ; 刷新所有用户桌面快捷方式（perMachine 安装模式）
  SetShellVarContext all
  System::Call "shell32::SHChangeNotify(i 0x2000, i 0x1005, t '$DESKTOP\${PRODUCTNAME}.lnk', i 0)"
  SetShellVarContext current

  ; 全局广播（同步），兜底清除其他残留缓存
  System::Call "shell32::SHChangeNotify(i 0x8000000, i 0x1000, i 0, i 0)"
!macroend
