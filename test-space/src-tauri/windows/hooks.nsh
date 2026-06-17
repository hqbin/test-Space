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
