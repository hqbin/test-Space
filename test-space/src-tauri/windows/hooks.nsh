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
  ; --- 强制重建桌面快捷方式（覆盖安装时 Tauri 会跳过重建，导致图标缓存不刷新）---
  ; 先删除再创建，Shell 必须重新从 exe 读取图标
  Delete "$DESKTOP\${PRODUCTNAME}.lnk"
  CreateShortcut "$DESKTOP\${PRODUCTNAME}.lnk" "$INSTDIR\${MAINBINARYNAME}.exe"
  !insertmacro SetLnkAppUserModelId "$DESKTOP\${PRODUCTNAME}.lnk"

  ; 开始菜单快捷方式同理
  Delete "$SMPROGRAMS\${PRODUCTNAME}.lnk"
  CreateShortcut "$SMPROGRAMS\${PRODUCTNAME}.lnk" "$INSTDIR\${MAINBINARYNAME}.exe"
  !insertmacro SetLnkAppUserModelId "$SMPROGRAMS\${PRODUCTNAME}.lnk"

  ; 通知 Shell exe 文件已更新（失效图标缓存条目）
  System::Call "shell32::SHChangeNotify(i 0x2000, i 0x1005, t '$INSTDIR\${MAINBINARYNAME}.exe', i 0)"

  ; 通知桌面快捷方式变更
  System::Call "shell32::SHChangeNotify(i 0x2000, i 0x1005, t '$DESKTOP\${PRODUCTNAME}.lnk', i 0)"

  ; 全局广播兜底
  System::Call "shell32::SHChangeNotify(i 0x8000000, i 0x1000, i 0, i 0)"

  ; 强制 Shell 重新加载图标资源
  nsExec::Exec '"$WINDIR\system32\ie4uinit.exe" -show'
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  ; 确保卸载时删除所有快捷方式（两种上下文都处理）
  Delete "$DESKTOP\${PRODUCTNAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCTNAME}.lnk"
  SetShellVarContext all
  Delete "$DESKTOP\${PRODUCTNAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCTNAME}.lnk"
  SetShellVarContext current
!macroend
