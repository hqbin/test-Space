/**
 * 本地代理服务
 * 用于与用户电脑上的 ADB 代理通信
 */

const LOCAL_AGENT_URL = 'http://localhost:9527';

export interface AdbCommand {
  command: string;
  args: string[];
}

export interface AdbResponse {
  success: boolean;
  output: string;
  error: string;
}

export interface AgentVersion {
  version: string;
  name: string;
}

/**
 * 检测本地代理是否运行
 */
export async function detectLocalAgent(): Promise<boolean> {
  try {
    const response = await fetch(`${LOCAL_AGENT_URL}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(2000), // 2秒超时
    });
    return response.ok;
  } catch (error) {
    return false;
  }
}

/**
 * 获取代理版本信息
 */
export async function getAgentVersion(): Promise<AgentVersion | null> {
  try {
    const response = await fetch(`${LOCAL_AGENT_URL}/version`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

/**
 * 检查更新
 */
export async function checkForUpdates(): Promise<any | null> {
  try {
    // 获取当前版本
    const currentVersion = await getAgentVersion();
    
    // 获取最新版本信息
    const response = await fetch('/adb-tool/api/agent/latest-version.json');
    if (!response.ok) return null;
    
    const latestInfo = await response.json();
    
    // 返回更新信息（包含当前版本）
    return {
      ...latestInfo,
      currentVersion: currentVersion?.version || '未知',
      hasUpdate: currentVersion && latestInfo.version !== currentVersion.version,
    };
  } catch (error) {
    return null;
  }
}

/**
 * 执行 ADB 命令
 */
export async function executeAdbCommand(args: string[]): Promise<AdbResponse> {
  try {
    const response = await fetch(`${LOCAL_AGENT_URL}/adb`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        command: 'adb',
        args,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    return {
      success: false,
      output: '',
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * 执行任意 shell 命令
 */
export async function executeShellCommand(command: string): Promise<AdbResponse> {
  try {
    const response = await fetch(`${LOCAL_AGENT_URL}/shell`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        command,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    return {
      success: false,
      output: '',
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * 获取设备列表
 */
export async function getDevices() {
  return executeAdbCommand(['devices', '-l']);
}

/**
 * 连接设备
 */
export async function connectDevice(ip: string, port: number = 5555) {
  const result = await executeAdbCommand(['connect', `${ip}:${port}`]);
  
  // adb connect 命令即使连接失败也会返回成功状态码
  // 需要检查输出内容来判断是否真的连接成功
  if (result.success) {
    const output = result.output.toLowerCase();
    
    // 检查是否包含成功的关键词
    if (output.includes('connected') || output.includes('already connected')) {
      return result;
    }
    
    // 检查是否包含失败的关键词
    if (output.includes('cannot connect') || 
        output.includes('connection refused') || 
        output.includes('no route to host') ||
        output.includes('failed') ||
        output.includes('timeout')) {
      return {
        success: false,
        output: result.output,
        error: '连接失败: ' + result.output.trim(),
      };
    }
    
    // 其他情况，返回原始结果
    return result;
  }
  
  return result;
}

/**
 * 断开设备
 */
export async function disconnectDevice(deviceId: string) {
  return executeAdbCommand(['disconnect', deviceId]);
}

/**
 * 获取设备信息
 */
export async function getDeviceInfo(deviceId: string) {
  // 获取设备属性
  const propsResult = await executeAdbCommand(['-s', deviceId, 'shell', 'getprop']);
  
  if (!propsResult.success) {
    return propsResult;
  }
  
  // 解析属性
  const props: Record<string, string> = {};
  const lines = propsResult.output.split('\n');
  
  for (const line of lines) {
    const match = line.match(/\[(.*?)\]: \[(.*?)\]/);
    if (match) {
      props[match[1]] = match[2];
    }
  }
  
  // 获取屏幕分辨率
  const wmResult = await executeAdbCommand(['-s', deviceId, 'shell', 'wm', 'size']);
  let resolution = '';
  if (wmResult.success) {
    const sizeMatch = wmResult.output.match(/Physical size: (\d+x\d+)/);
    if (sizeMatch) {
      resolution = sizeMatch[1];
    }
  }
  
  // 获取屏幕密度
  const densityResult = await executeAdbCommand(['-s', deviceId, 'shell', 'wm', 'density']);
  let density = '';
  if (densityResult.success) {
    const densityMatch = densityResult.output.match(/Physical density: (\d+)/);
    if (densityMatch) {
      density = densityMatch[1];
    }
  }
  
  return {
    success: true,
    output: JSON.stringify({
      device_id: deviceId,
      status: 'device',
      model: props['ro.product.model'] || '',
      manufacturer: props['ro.product.manufacturer'] || '',
      android_version: props['ro.build.version.release'] || '',
      sdk_version: props['ro.build.version.sdk'] || '',
      build_fingerprint: props['ro.build.fingerprint'] || '',
      resolution,
      density,
    }),
    error: '',
  };
}

/**
 * 获取已安装应用列表
 */
export async function getInstalledApps(deviceId: string, includeSystem: boolean = false) {
  const args = ['-s', deviceId, 'shell', 'pm', 'list', 'packages'];
  if (!includeSystem) {
    args.push('-3'); // 只显示第三方应用
  }
  
  const result = await executeAdbCommand(args);
  
  if (!result.success) {
    return result;
  }
  
  // 解析应用列表
  const apps = result.output
    .split('\n')
    .filter(line => line.startsWith('package:'))
    .map(line => line.replace('package:', '').trim())
    .filter(pkg => pkg);
  
  return {
    success: true,
    output: JSON.stringify(apps),
    error: '',
  };
}

/**
 * 安装 APK
 */
export async function installApk(deviceId: string, apkPath: string) {
  return executeAdbCommand(['-s', deviceId, 'install', '-r', apkPath]);
}

/**
 * 卸载应用
 */
export async function uninstallApp(deviceId: string, packageName: string) {
  return executeAdbCommand(['-s', deviceId, 'uninstall', packageName]);
}

/**
 * 启动应用
 */
export async function startApp(deviceId: string, packageName: string) {
  return executeAdbCommand(['-s', deviceId, 'shell', 'monkey', '-p', packageName, '-c', 'android.intent.category.LAUNCHER', '1']);
}

/**
 * 停止应用
 */
export async function stopApp(deviceId: string, packageName: string) {
  return executeAdbCommand(['-s', deviceId, 'shell', 'am', 'force-stop', packageName]);
}

/**
 * 清除应用数据
 */
export async function clearAppData(deviceId: string, packageName: string) {
  return executeAdbCommand(['-s', deviceId, 'shell', 'pm', 'clear', packageName]);
}

/**
 * 截图
 */
export async function takeScreenshot(deviceId: string) {
  return executeAdbCommand(['-s', deviceId, 'exec-out', 'screencap', '-p']);
}

/**
 * 开始录屏
 */
export async function startRecording(deviceId: string, filename: string) {
  return executeAdbCommand(['-s', deviceId, 'shell', 'screenrecord', `/sdcard/${filename}`]);
}

/**
 * 停止录屏（通过发送 Ctrl+C）
 */
export async function stopRecording(deviceId: string) {
  // 注意：这个需要特殊处理，可能需要通过 shell 命令 kill 进程
  return executeAdbCommand(['-s', deviceId, 'shell', 'pkill', '-SIGINT', 'screenrecord']);
}

/**
 * 拉取文件
 */
export async function pullFile(deviceId: string, remotePath: string, localPath: string) {
  return executeAdbCommand(['-s', deviceId, 'pull', remotePath, localPath]);
}

/**
 * 推送文件
 */
export async function pushFile(deviceId: string, localPath: string, remotePath: string) {
  return executeAdbCommand(['-s', deviceId, 'push', localPath, remotePath]);
}

/**
 * 获取 logcat
 */
export async function getLogcat(deviceId: string, filter?: string) {
  const args = ['-s', deviceId, 'logcat', '-d'];
  if (filter) {
    args.push(filter);
  }
  return executeAdbCommand(args);
}

/**
 * 清除 logcat
 */
export async function clearLogcat(deviceId: string) {
  return executeAdbCommand(['-s', deviceId, 'logcat', '-c']);
}

/**
 * 生成 bugreport
 */
export async function generateBugreport(deviceId: string, outputPath: string) {
  return executeAdbCommand(['-s', deviceId, 'bugreport', outputPath]);
}

/**
 * 发送按键事件
 */
export async function sendKeyevent(deviceId: string, keycode: number) {
  return executeAdbCommand(['-s', deviceId, 'shell', 'input', 'keyevent', keycode.toString()]);
}

/**
 * 发送文本输入
 */
export async function sendText(deviceId: string, text: string) {
  // 转义特殊字符
  const escapedText = text.replace(/\s/g, '%s');
  return executeAdbCommand(['-s', deviceId, 'shell', 'input', 'text', escapedText]);
}

/**
 * 发送触摸事件
 */
export async function sendTap(deviceId: string, x: number, y: number) {
  return executeAdbCommand(['-s', deviceId, 'shell', 'input', 'tap', x.toString(), y.toString()]);
}

/**
 * 发送滑动事件
 */
export async function sendSwipe(deviceId: string, x1: number, y1: number, x2: number, y2: number, duration: number = 300) {
  return executeAdbCommand(['-s', deviceId, 'shell', 'input', 'swipe', x1.toString(), y1.toString(), x2.toString(), y2.toString(), duration.toString()]);
}

/**
 * 执行 ADB shell 命令
 */
export async function executeAdbShellCommand(deviceId: string, command: string) {
  return executeAdbCommand(['-s', deviceId, 'shell', command]);
}

/**
 * 重启设备
 */
export async function rebootDevice(deviceId: string) {
  return executeAdbCommand(['-s', deviceId, 'reboot']);
}

/**
 * 重启到 recovery 模式
 */
export async function rebootToRecovery(deviceId: string) {
  return executeAdbCommand(['-s', deviceId, 'reboot', 'recovery']);
}

/**
 * 重启到 bootloader 模式
 */
export async function rebootToBootloader(deviceId: string) {
  return executeAdbCommand(['-s', deviceId, 'reboot', 'bootloader']);
}

/**
 * Root 设备
 */
export async function rootDevice(deviceId: string) {
  return executeAdbCommand(['-s', deviceId, 'root']);
}

/**
 * Remount 设备
 */
export async function remountDevice(deviceId: string) {
  return executeAdbCommand(['-s', deviceId, 'remount']);
}

/**
 * 重启 ADB 服务
 */
export async function restartAdb() {
  // 先 kill-server
  const killResult = await executeAdbCommand(['kill-server']);
  if (!killResult.success) {
    return killResult;
  }
  
  // 等待一下
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // 再 start-server
  return executeAdbCommand(['start-server']);
}

/**
 * 输入文本（使用 input text）
 */
export async function inputText(deviceId: string, text: string) {
  // 转义特殊字符
  const escapedText = text.replace(/\s/g, '%s');
  return executeAdbCommand(['-s', deviceId, 'shell', 'input', 'text', escapedText]);
}

/**
 * 获取设备基础信息（返回键值对数组）
 * 与后端逻辑完全一致
 */
export async function getDeviceBasicInfo(deviceId: string) {
  const basicInfo = [];
  
  try {
    // 设备名
    let result = await executeAdbCommand(['-s', deviceId, 'shell', 'getprop', 'ro.product.name']);
    if (result.success && result.output) {
      basicInfo.push({ key: '设备名', value: result.output.trim() });
    }
    
    // 型号
    result = await executeAdbCommand(['-s', deviceId, 'shell', 'getprop', 'ro.product.model']);
    if (result.success && result.output) {
      basicInfo.push({ key: '型号', value: result.output.trim() });
    }
    
    // Android版本
    result = await executeAdbCommand(['-s', deviceId, 'shell', 'getprop', 'ro.build.version.release']);
    if (result.success && result.output) {
      basicInfo.push({ key: 'Android版本', value: result.output.trim() });
    }
    
    // DPI
    result = await executeAdbCommand(['-s', deviceId, 'shell', 'wm', 'density']);
    if (result.success) {
      basicInfo.push({ key: 'DPI', value: result.output.trim() });
    }
    
    // 分辨率
    result = await executeAdbCommand(['-s', deviceId, 'shell', 'wm', 'size']);
    if (result.success) {
      basicInfo.push({ key: '分辨率', value: result.output.trim() });
    }
    
    // 运行内存
    result = await executeAdbCommand(['-s', deviceId, 'shell', 'free', '-h']);
    if (result.success) {
      const lines = result.output.trim().split('\n');
      if (lines.length > 1) {
        const memLine = lines[1].split(/\s+/);
        if (memLine.length > 1) {
          basicInfo.push({ key: '运行内存', value: memLine[1] });
        }
      }
    }
    
    // 本地Mac
    result = await executeAdbCommand(['-s', deviceId, 'shell', 'cat', '/sys/class/net/eth0/address']);
    if (result.success && result.output) {
      basicInfo.push({ key: '本地Mac', value: result.output.trim() });
    }
    
    // 网络Mac
    result = await executeAdbCommand(['-s', deviceId, 'shell', 'cat', '/sys/class/net/wlan0/address']);
    if (result.success && result.output) {
      basicInfo.push({ key: '网络Mac', value: result.output.trim() });
    }
    
    // 物理存储容量
    result = await executeAdbCommand(['-s', deviceId, 'shell', 'cat', '/sys/block/mmcblk0/size']);
    if (result.success && result.output) {
      try {
        const sectors = parseInt(result.output.trim());
        const bytesSize = sectors * 512;
        const gbSize = (bytesSize / (1024 * 1024 * 1024)).toFixed(2);
        const mbSize = (bytesSize / (1024 * 1024)).toFixed(2);
        basicInfo.push({ key: '物理存储容量', value: `${gbSize}G(${mbSize}MB)` });
      } catch (e) {
        // Ignore parse errors
      }
    }
    
    // Storage - usage
    result = await executeAdbCommand(['-s', deviceId, 'shell', 'df', '/data']);
    if (result.success) {
      const lines = result.output.trim().split('\n');
      if (lines.length > 1) {
        const parts = lines[1].split(/\s+/);
        if (parts.length >= 4) {
          try {
            const totalKb = parseFloat(parts[1]);
            const availKb = parseFloat(parts[3]);
            
            const totalGb = (totalKb / (1024 * 1024)).toFixed(2);
            const availGb = (availKb / (1024 * 1024)).toFixed(2);
            
            const totalMb = (totalKb / 1024).toFixed(2);
            const availMb = (availKb / 1024).toFixed(2);
            
            basicInfo.push({ key: '可使用总存储空间', value: `${totalGb}G(${totalMb}MB)` });
            basicInfo.push({ key: '剩余存储空间', value: `${availGb}G(${availMb}MB)` });
          } catch (e) {
            // Ignore parse errors
          }
        }
      }
    }
    
    return {
      success: true,
      output: JSON.stringify(basicInfo),
      error: '',
    };
  } catch (error) {
    return {
      success: false,
      output: '',
      error: error instanceof Error ? error.message : 'Failed to get device basic info',
    };
  }
}

/**
 * 获取固件信息（WhaleOS）
 * 与后端逻辑完全一致
 */
export async function getDeviceFirmwareInfo(deviceId: string) {
  // Root device first
  await executeAdbCommand(['-s', deviceId, 'root']);
  
  // Default WhaleTV firmware keys (from backend)
  const osaKeys = [
    'ro.product.model',
    'ro.product.tv.rcu',
    'ro.product.tv.deviceType',
    'ro.vendor.product.version',
    'ro.vendor.zeasn.firmwareID',
    'persist.sys.cur_country',
    'persist.sys.cur_language',
    'ro.product.tv.def.country',
    'ro.product.tv.language.list',
    'ro.product.tv.country.list',
    'ro.boot.pid',
    'ro.boot.mac'
  ];
  
  const info: Record<string, string> = {};
  
  for (const key of osaKeys) {
    const result = await executeAdbCommand(['-s', deviceId, 'shell', 'getprop', key]);
    if (result.success && result.output) {
      const output = result.output.trim();
      if (output && !output.toLowerCase().includes('not found') && !output.toLowerCase().includes('offline')) {
        info[key] = output;
      }
    }
  }
  
  return {
    success: true,
    output: JSON.stringify(info),
    error: '',
  };
}

/**
 * 获取 AOSP 固件信息
 * 与后端逻辑完全一致
 */
export async function getAospFirmwareInfo(deviceId: string) {
  const info = {
    firmware: {} as Record<string, string>,
    dp: {} as Record<string, string>,
    adservice: {
      status: '',
      version_info: '',
    },
  };
  
  try {
    // Root device first
    await executeAdbCommand(['-s', deviceId, 'root']);
    
    // Firmware info (gj_keys) - 与后端完全一致
    const gjKeys = [
      'ro.product.model',
      'ro.build.display.id',
      'ro.tv.default.country',
      'ro.build.description',
      'ro.vendor.product.version'
    ];
    
    for (const key of gjKeys) {
      const result = await executeAdbCommand(['-s', deviceId, 'shell', 'getprop', key]);
      if (result.success && result.output) {
        const output = result.output.trim();
        if (output && !output.toLowerCase().includes('not found') && !output.toLowerCase().includes('offline')) {
          info.firmware[key] = output;
        }
      }
    }
    
    // DP info (dp_keys) - 与后端完全一致（完整30个）
    const dpKeys = [
      'ro.product.devicetype',
      'ro.devicetype.zeasn',
      'mtk.zeasn.devicetype',
      'ro.jview.devicetyp',
      'ro.build.product',
      'persist.zvt.devicetype',
      'ro.product.model',
      'ro.tcl.client.type',
      'ro.zeasn.devicetype',
      'ro.Zeasn.devicetype',
      'ro.vendor.zeasn.devicetype',
      'ro.newlink.cusname',
      'ro.wwt.product.name',
      'ro.product.device',
      'ro.stellamore.devicetype',
      'ro.htc.devicetype',
      'persist.Zeasn.devicetype',
      'ro.zoc.devicetype',
      'ro.country.zeasn',
      'ro.jixin.devicetype',
      'ro.talents.zeasn.devicetype',
      'ro.sl.devicetype',
      'ro.lc.zeasn.devicetype',
      'ro.cnd.devicetype',
      'ro.product.mode',
      'persist.zeasn.devicetype',
      'ro.jixin.device_type',
      'ro.yhksn.devicetype',
      'ro.odm.changhong.devicetype',
      'ro.cvte.customer',
      'ro.fanghua.devicetype'
    ];
    
    for (const key of dpKeys) {
      const result = await executeAdbCommand(['-s', deviceId, 'shell', 'getprop', key]);
      if (result.success && result.output) {
        const output = result.output.trim();
        if (output && !output.toLowerCase().includes('not found') && !output.toLowerCase().includes('offline')) {
          info.dp[key] = output;
        }
      }
    }
    
    // ADService detection
    const result = await executeAdbCommand(['-s', deviceId, 'shell', 'pm', 'list', 'package', '-3']);
    
    if (result.success) {
      const packages = result.output;
      
      // Check for com.ad.socketserver
      if (packages.includes('com.ad.socketserver')) {
        info.adservice.status = '检测到设备中有安装ADServices: com.ad.socketserver';
        
        // Get version info
        const versionResult = await executeAdbCommand(['-s', deviceId, 'shell', 'dumpsys', 'package', 'com.ad.socketserver']);
        if (versionResult.success) {
          // Extract version info
          const lines = versionResult.output.split('\n');
          for (const line of lines) {
            if (line.toLowerCase().includes('version')) {
              info.adservice.version_info = line.trim();
              break;
            }
          }
        }
      }
      // Check for com.android.media.module.services
      else if (packages.includes('com.android.media.module.services')) {
        info.adservice.status = '检测到设备中有安装ADServices: com.android.media.module.services';
        
        // Get version info
        const versionResult = await executeAdbCommand(['-s', deviceId, 'shell', 'dumpsys', 'package', 'com.android.media.module.services']);
        if (versionResult.success) {
          // Extract version info
          const lines = versionResult.output.split('\n');
          for (const line of lines) {
            if (line.toLowerCase().includes('version')) {
              info.adservice.version_info = line.trim();
              break;
            }
          }
        }
      }
      else {
        info.adservice.status = '没有检测到设备中有ADServices';
      }
    }
    
    return {
      success: true,
      output: JSON.stringify(info),
      error: '',
    };
  } catch (error) {
    return {
      success: false,
      output: '',
      error: error instanceof Error ? error.message : 'Failed to get AOSP firmware info',
    };
  }
}

/**
 * 检查设备 Key 烧写情况
 * 与后端逻辑完全一致
 */
export async function checkDeviceKeys(deviceId: string) {
  const results = [];
  
  try {
    // Root device first
    await executeAdbCommand(['-s', deviceId, 'root']);
    
    // Define keys to check (与后端完全一致)
    const keysToCheck = [
      {
        name: 'HDCP1.4',
        command: ['shell', 'tee_provision', '-qt', '0x31'],
        successMsg: '检测到设备支持HDCP1.4',
        failMsg: '检测到设备不支持HDCP1.4',
        warning: '警告: HDCP1.4未烧写将导致无法播放受保护的高清内容',
        type: 'tee'
      },
      {
        name: 'HDCP2.2',
        command: ['shell', 'tee_provision', '-qt', '0x32'],
        successMsg: '检测到设备支持HDCP2.2',
        failMsg: '检测到设备不支持HDCP2.2',
        warning: '警告: HDCP2.2未烧写将导致无法播放4K超高清内容',
        type: 'tee'
      },
      {
        name: 'MGKID',
        command: ['shell', 'tee_provision', '-qt', '0xa2'],
        successMsg: '检测到设备支持MGKID',
        failMsg: '检测到设备不支持MGKID',
        warning: '警告: MGKID未烧写将影响某些DRM内容的播放',
        type: 'tee'
      },
      {
        name: 'Widevine',
        command: ['shell', 'drminfo', '-d'],
        successMsg: '检测到设备支持Widevine',
        failMsg: '检测到设备不支持Widevine',
        warning: '警告: Widevine未授权将导致无法打开Netflix、D+、Primevideo',
        type: 'widevine'
      },
      {
        name: 'Dolby',
        command: ['shell', 'dolby_fw_dolbyms12', '/oem/lib/ms12/libdolbyms12.so', '/data/test.so'],
        successMsg: '检测到设备支持Dolby',
        failMsg: '检测到设备不支持Dolby',
        warning: '警告: Dolby未正常工作将影响音频输出质量',
        type: 'dolby'
      }
    ];
    
    // Check each key
    for (const keyInfo of keysToCheck) {
      try {
        const result = await executeAdbCommand(['-s', deviceId, ...keyInfo.command]);
        
        let isSuccess = false;
        // Get output from both stdout and stderr
        let output = result.output || '';
        if (result.error && !output.includes(result.error)) {
          output = output ? output + '\n' + result.error : result.error;
        }
        
        // Check based on key type
        if (keyInfo.type === 'tee') {
          // tee_provision type check
          if (output) {
            isSuccess = output.includes('provisioned') && !output.includes('not provisioned');
            isSuccess = isSuccess || output.toLowerCase().includes('success') || output.includes('已配置');
          }
        } else if (keyInfo.type === 'widevine') {
          // Widevine check - look for systemId
          if (output) {
            const match = output.match(/systemId[=\s]+([0-9]{5})/);
            isSuccess = !!match;
            if (!isSuccess) {
              isSuccess = /\d/.test(output);
            }
          }
        } else if (keyInfo.type === 'dolby') {
          // Dolby check - look for exits! and done!
          if (output) {
            isSuccess = output.includes('exits!') && output.includes('done!');
          }
        }
        
        results.push({
          name: keyInfo.name,
          status: isSuccess ? 'success' : 'fail',
          message: isSuccess ? keyInfo.successMsg : keyInfo.failMsg,
          warning: isSuccess ? null : keyInfo.warning,
          output: output.trim() || '(无输出)'
        });
      } catch (error) {
        results.push({
          name: keyInfo.name,
          status: 'error',
          message: `${keyInfo.name}检测出错`,
          warning: error instanceof Error ? error.message : 'Unknown error',
          output: ''
        });
      }
    }
    
    return {
      success: true,
      output: JSON.stringify(results),
      error: '',
    };
  } catch (error) {
    return {
      success: false,
      output: '',
      error: error instanceof Error ? error.message : 'Failed to check device keys',
    };
  }
}

/**
 * 获取应用版本信息
 */
export async function getAppVersion(deviceId: string, packageName: string) {
  const result = await executeAdbCommand(['-s', deviceId, 'shell', 'dumpsys', 'package', packageName]);
  
  if (!result.success) {
    return result;
  }
  
  // 解析版本信息
  let versionName = '';
  let versionCode = '';
  
  const lines = result.output.split('\n');
  for (const line of lines) {
    if (line.includes('versionName=')) {
      const match = line.match(/versionName=([^\s]+)/);
      if (match) versionName = match[1];
    }
    if (line.includes('versionCode=')) {
      const match = line.match(/versionCode=(\d+)/);
      if (match) versionCode = match[1];
    }
  }
  
  return {
    success: true,
    output: JSON.stringify({
      version_name: versionName,
      version_code: parseInt(versionCode) || 0,
    }),
    error: '',
  };
}

/**
 * 修改设备配置
 * 实现逻辑：
 * 1. 如果没有指定路径，自动查找包含该 key 的配置文件
 * 2. Pull 配置文件到本地代理
 * 3. 在本地修改文件内容（支持 JSON 和普通文本格式）
 * 4. Push 修改后的文件回设备
 */
export async function modifyDeviceConfig(
  deviceId: string,
  configPath: string,
  configKey: string,
  configValue: string
) {
  try {
    const response = await fetch(`${LOCAL_AGENT_URL}/config/modify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        device_id: deviceId,
        config_path: configPath,
        config_key: configKey,
        config_value: configValue,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    return {
      success: false,
      output: '',
      error: error instanceof Error ? error.message : 'Failed to modify config',
    };
  }
}

/**
 * ========================================
 * 文件上传和下载功能
 * ========================================
 */

/**
 * 上传并安装 APK
 */
export async function uploadAndInstallApk(
  deviceId: string,
  file: File,
  reinstall: boolean = false,
): Promise<AdbResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('device_id', deviceId);
    formData.append('reinstall', reinstall ? 'true' : 'false');

    const response = await fetch(`${LOCAL_AGENT_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    return {
      success: false,
      output: '',
      error: error instanceof Error ? error.message : 'Upload failed',
    };
  }
}

/**
 * 推送文件到设备
 */
export async function pushFileToDevice(deviceId: string, file: File, remotePath: string): Promise<AdbResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('device_id', deviceId);
    formData.append('remote_path', remotePath);

    const response = await fetch(`${LOCAL_AGENT_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    return {
      success: false,
      output: '',
      error: error instanceof Error ? error.message : 'Push failed',
    };
  }
}

/**
 * 下载截图
 */
export async function downloadScreenshot(deviceId: string): Promise<Blob> {
  const response = await fetch(
    `${LOCAL_AGENT_URL}/download?device_id=${encodeURIComponent(deviceId)}&type=screenshot`
  );

  if (!response.ok) {
    throw new Error(`Failed to download screenshot: ${response.statusText}`);
  }

  return await response.blob();
}

/**
 * 下载录屏文件
 */
export async function downloadRecording(deviceId: string, filename: string): Promise<Blob> {
  const remotePath = `/sdcard/${filename}`;
  const response = await fetch(
    `${LOCAL_AGENT_URL}/download?device_id=${encodeURIComponent(deviceId)}&remote_path=${encodeURIComponent(remotePath)}`
  );

  if (!response.ok) {
    throw new Error(`Failed to download recording: ${response.statusText}`);
  }

  return await response.blob();
}

/**
 * 下载 APK
 */
export async function downloadApk(deviceId: string, packageName: string): Promise<Blob> {
  // 首先获取 APK 路径
  const pathResult = await executeAdbCommand(['-s', deviceId, 'shell', 'pm', 'path', packageName]);
  
  if (!pathResult.success) {
    throw new Error('Failed to get APK path');
  }

  // 解析路径
  const match = pathResult.output.match(/package:(.+)/);
  if (!match) {
    throw new Error('Invalid APK path format');
  }

  const remotePath = match[1].trim();

  // 下载 APK
  const response = await fetch(
    `${LOCAL_AGENT_URL}/download?device_id=${encodeURIComponent(deviceId)}&remote_path=${encodeURIComponent(remotePath)}`
  );

  if (!response.ok) {
    throw new Error(`Failed to download APK: ${response.statusText}`);
  }

  return await response.blob();
}

/**
 * ========================================
 * 会话管理功能
 * ========================================
 */

export interface SessionResponse {
  success: boolean;
  session_id?: string;
  message?: string;
  error?: string;
}

export interface SessionStatus {
  success: boolean;
  session_id: string;
  device_id: string;
  type: string;
  running: boolean;
  start_time: string;
  duration: number;
}

/**
 * 启动 logcat 会话
 */
export async function startLogcatSession(deviceId: string, filter?: string): Promise<SessionResponse> {
  try {
    const response = await fetch(`${LOCAL_AGENT_URL}/session/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        device_id: deviceId,
        type: 'logcat',
        filter,
      }),
      signal: AbortSignal.timeout(60000),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to start logcat session',
    };
  }
}

/**
 * 停止 logcat 会话并下载日志
 */
export async function stopLogcatSession(sessionId: string): Promise<Blob> {
  const response = await fetch(`${LOCAL_AGENT_URL}/session/stop`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to stop logcat session: ${response.statusText}`);
  }

  return await response.blob();
}

/**
 * 获取 logcat 会话状态
 */
export async function getLogcatSessionStatus(sessionId: string): Promise<SessionStatus> {
  const response = await fetch(
    `${LOCAL_AGENT_URL}/session/status?session_id=${encodeURIComponent(sessionId)}`
  );

  if (!response.ok) {
    throw new Error(`Failed to get session status: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * 启动录屏会话
 */
export async function startRecordingSession(deviceId: string, filename: string): Promise<SessionResponse> {
  try {
    const response = await fetch(`${LOCAL_AGENT_URL}/session/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        device_id: deviceId,
        type: 'recording',
        filename,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to start recording session',
    };
  }
}

/**
 * 停止录屏会话并下载视频
 */
export async function stopRecordingSession(sessionId: string, deviceId?: string): Promise<Blob> {
  const url = deviceId
    ? `${LOCAL_AGENT_URL}/session/stop?device_id=${encodeURIComponent(deviceId)}`
    : `${LOCAL_AGENT_URL}/session/stop`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `Failed to stop recording session: ${response.statusText}`;
    try {
      const errorData = JSON.parse(errorText);
      if (errorData.error) {
        errorMessage = errorData.error;
      }
    } catch {
      // Not JSON, use default message
    }
    throw new Error(errorMessage);
  }

  return await response.blob();
}

/**
 * 获取录屏会话状态
 */
export async function getRecordingSessionStatus(sessionId: string): Promise<SessionStatus> {
  const response = await fetch(
    `${LOCAL_AGENT_URL}/session/status?session_id=${encodeURIComponent(sessionId)}`
  );

  if (!response.ok) {
    throw new Error(`Failed to get session status: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * ========================================
 * WebSocket 屏幕镜像
 * ========================================
 */

export interface ScreenMirrorConnection {
  close: () => void;
}

/**
 * 连接屏幕镜像
 */
export function connectScreenMirror(
  deviceId: string,
  onFrame: (blob: Blob) => void,
  onError?: (error: Error) => void,
  onClose?: () => void,
  options?: {
    fps?: number;      // 帧率 (1-30)
    maxSize?: number;  // 最大分辨率 (480-3840)
  }
): ScreenMirrorConnection {
  // 构建 WebSocket URL，添加参数
  const params = new URLSearchParams({
    device_id: deviceId,
  });
  
  if (options?.fps) {
    params.append('fps', options.fps.toString());
  }
  
  if (options?.maxSize) {
    params.append('max_size', options.maxSize.toString());
  }
  
  const ws = new WebSocket(`ws://localhost:9527/ws/mirror?${params.toString()}`);
  
  ws.binaryType = 'blob';

  ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
      onFrame(event.data);
    }
  };

  ws.onerror = (event) => {
    console.error('WebSocket error:', event);
    onError?.(new Error('WebSocket connection error'));
  };

  ws.onclose = () => {
    console.log('WebSocket closed');
    onClose?.();
  };

  return {
    close: () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    },
  };
}

/**
 * ========================================
 * 代理更新功能
 * ========================================
 */

export interface UpdateInfo {
  latest_version: string;
  download_url: string;
  changelog: string;
  has_update: boolean;
}

/**
 * 检查代理更新
 */
export async function checkAgentUpdate(): Promise<UpdateInfo | null> {
  try {
    const response = await fetch(`${LOCAL_AGENT_URL}/update/check`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Failed to check agent update:', error);
    return null;
  }
}

/**
 * 触发代理更新
 */
export async function triggerAgentUpdate(): Promise<boolean> {
  try {
    const response = await fetch(`${LOCAL_AGENT_URL}/update/trigger`, {
      method: 'POST',
    });
    return response.ok;
  } catch (error) {
    console.error('Failed to trigger agent update:', error);
    return false;
  }
}

/**
 * 检查并自动更新代理（如果需要）
 * 返回是否触发了更新
 */
export async function checkAndUpdateAgent(): Promise<boolean> {
  try {
    const updateInfo = await checkAgentUpdate();
    
    if (!updateInfo) {
      console.log('Failed to check for updates');
      return false;
    }
    
    if (!updateInfo.has_update) {
      console.log('Agent is up to date');
      return false;
    }
    
    console.log(`New agent version available: ${updateInfo.latest_version}`);
    console.log(`Changelog: ${updateInfo.changelog}`);
    
    // 触发更新
    const success = await triggerAgentUpdate();
    
    if (success) {
      console.log('Agent update triggered, will restart shortly');
    } else {
      console.error('Failed to trigger agent update');
    }
    
    return success;
  } catch (error) {
    console.error('Error in checkAndUpdateAgent:', error);
    return false;
  }
}


/**
 * 关闭代理程序
 */
export async function shutdownAgent(): Promise<boolean> {
  try {
    const response = await fetch(`${LOCAL_AGENT_URL}/shutdown`, {
      method: 'POST',
    });
    return response.ok;
  } catch (error) {
    console.error('Failed to shutdown agent:', error);
    return false;
  }
}

/**
 * ========================================
 * 完整诊断日志采集
 * ========================================
 */

/**
 * 启动完整诊断日志采集
 */
export async function startDiagnosticLog(deviceId: string): Promise<SessionResponse> {
  try {
    const response = await fetch(`${LOCAL_AGENT_URL}/diagnostic/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        device_id: deviceId,
      }),
      signal: AbortSignal.timeout(60000),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to start diagnostic log',
    };
  }
}

/**
 * 停止完整诊断日志采集并下载
 */
export async function stopDiagnosticLog(sessionId: string): Promise<Blob> {
  const response = await fetch(`${LOCAL_AGENT_URL}/diagnostic/stop`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to stop diagnostic log: ${response.statusText}`);
  }

  return await response.blob();
}
