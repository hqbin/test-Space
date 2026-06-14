import React, { useEffect, useState } from 'react';
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  LinearProgress,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import ErrorIcon from '@mui/icons-material/Error';
import UpdateIcon from '@mui/icons-material/Update';
import { detectLocalAgent, getAgentVersion, checkForUpdates, shutdownAgent } from '../services/localAgent';

interface LocalAgentDetectorProps {
  children: React.ReactNode;
}

export const LocalAgentDetector: React.FC<LocalAgentDetectorProps> = ({ children }) => {
  const [agentRunning, setAgentRunning] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(true);
  const [updateRequired, setUpdateRequired] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<any>(null);
  const [downloading, setDownloading] = useState(false);
  const [downloaded, setDownloaded] = useState(false);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    checkAgentAndUpdate();
  }, []);

  // 轮询检测代理是否已安装/更新
  useEffect(() => {
    if (!polling) return;

    const pollInterval = setInterval(async () => {
      console.log('[LocalAgentDetector] Polling for agent...');
      const running = await detectLocalAgent();
      
      if (running) {
        console.log('[LocalAgentDetector] Agent detected! Checking version...');
        
        // 如果是更新场景，检查版本是否已更新
        if (updateRequired && updateInfo) {
          const currentVersion = await getAgentVersion();
          if (currentVersion && currentVersion.version === updateInfo.version) {
            console.log('[LocalAgentDetector] Version updated! Reloading page...');
            // 版本已更新，刷新页面
            window.location.reload();
          }
        } else {
          // 如果是首次安装，直接刷新
          console.log('[LocalAgentDetector] Agent installed! Reloading page...');
          window.location.reload();
        }
      }
    }, 2000); // 每 2 秒检测一次

    return () => clearInterval(pollInterval);
  }, [polling, updateRequired, updateInfo]);

  const checkAgentAndUpdate = async () => {
    // 检测代理是否运行
    const running = await detectLocalAgent();
    setAgentRunning(running);
    setChecking(false);
    
    if (running) {
      // 检查是否有新版本
      const currentVersion = await getAgentVersion();
      const latestInfo = await checkForUpdates();
      
      if (latestInfo && currentVersion && latestInfo.version !== currentVersion.version) {
        // 有新版本，强制更新
        setUpdateInfo(latestInfo);
        setUpdateRequired(true);
      }
    }
  };

  const handleDownloadUpdate = () => {
    setDownloading(true);
    
    // 检测操作系统和架构
    const platform = navigator.platform.toLowerCase();
    const userAgent = navigator.userAgent.toLowerCase();
    
    let downloadUrl = '/adb-tool/downloads/adb-agent-windows.exe';
    let filename = 'adb-agent-windows.exe';
    
    if (platform.includes('mac') || userAgent.includes('mac')) {
      // Mac 系统 - 检测芯片类型
      // 注意：浏览器无法直接检测 Mac 芯片类型，默认使用 Intel 版本（兼容 Rosetta 2）
      downloadUrl = '/adb-tool/downloads/adb-agent-mac';
      filename = 'adb-agent-mac';
    }
    
    // 创建下载链接
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // 下载完成后显示安装按钮并开始轮询
    setTimeout(() => {
      setDownloading(false);
      setDownloaded(true);
      setPolling(true); // 开始轮询检测
    }, 2000);
  };

  const handleInstall = async () => {
    const isWindows = navigator.platform.toLowerCase().includes('win');
    
    // 先尝试关闭旧版本代理
    try {
      await shutdownAgent();
      
      // 等待代理完全关闭
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 提示用户运行新版本
      const steps = isWindows 
        ? `旧版本代理已关闭，请按照以下步骤完成安装：

1. 找到刚才下载的文件
   位置：通常在"下载"文件夹
   文件名：adb-agent-windows.exe

2. 运行新版本
   - 双击 adb-agent-windows.exe
   - 如果 Windows 提示"是否保留此应用"，选择"保留"
   - 如果提示"Windows 已保护你的电脑"，点击"更多信息" → "仍要运行"

3. 刷新此页面
   - 按 Ctrl+F5 强制刷新
   - 或者关闭浏览器重新打开`
        : `旧版本代理已关闭，请按照以下步骤完成安装：

1. 找到刚才下载的文件
   位置：通常在"下载"文件夹
   文件名：adb-agent-mac

2. 运行新版本
   - 双击 adb-agent-mac
   - 如果提示"无法打开"，打开"系统偏好设置" → "安全性与隐私" → "仍要打开"

3. 刷新此页面
   - 按 Cmd+Shift+R 强制刷新
   - 或者关闭浏览器重新打开`;

      alert(steps);
    } catch (error) {
      // 如果关闭失败（可能代理已经关闭或无法连接），提示手动关闭
      const steps = isWindows 
        ? `请按照以下步骤安装：

1. 找到刚才下载的文件
   位置：通常在"下载"文件夹
   文件名：adb-agent-windows.exe

2. 【重要】先关闭旧版本代理
   - 在任务栏右下角托盘区找到代理图标
   - 右键点击图标
   - 选择"退出"或"Exit"
   - 等待程序完全关闭

3. 运行新下载的文件
   - 双击 adb-agent-windows.exe
   - 如果 Windows 提示"是否保留此应用"，选择"保留"
   - 如果提示"Windows 已保护你的电脑"，点击"更多信息" → "仍要运行"

4. 刷新此页面
   - 按 Ctrl+F5 强制刷新
   - 或者关闭浏览器重新打开

注意：如果提示"文件正在被使用"，说明旧版本还没有完全关闭，请重新执行第2步。`
        : `请按照以下步骤安装：

1. 找到刚才下载的文件
   位置：通常在"下载"文件夹
   文件名：adb-agent-mac

2. 【重要】先关闭旧版本代理
   - 在菜单栏找到代理图标
   - 点击图标
   - 选择"退出"或"Quit"
   - 等待程序完全关闭

3. 运行新下载的文件
   - 双击 adb-agent-mac
   - 如果提示"无法打开"，打开"系统偏好设置" → "安全性与隐私" → "仍要打开"

4. 刷新此页面
   - 按 Cmd+Shift+R 强制刷新
   - 或者关闭浏览器重新打开`;

      alert(steps);
    }
  };

  // 正在检测
  if (checking && agentRunning === null) {
    return null;
  }

  // 代理未运行
  if (!agentRunning) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        p={3}
      >
        <Alert severity="warning" sx={{ maxWidth: 600, mb: 3 }}>
          <AlertTitle>
            <Box display="flex" alignItems="center">
              <ErrorIcon sx={{ mr: 1 }} />
              需要本地代理
            </Box>
          </AlertTitle>
          <Typography variant="body2">
            为了连接和操作您本地的 ADB 设备，需要在您的电脑上运行一个轻量级代理程序。
          </Typography>
        </Alert>

        <Box sx={{ maxWidth: 600, width: '100%' }}>
          <Typography variant="h6" gutterBottom>
            下载本地代理
          </Typography>

          <Box display="flex" flexDirection="column" gap={2} mb={3}>
            {/* Windows 版本 */}
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              href="/adb-tool/downloads/adb-agent-windows.exe"
              download
              onClick={() => setPolling(true)}
              fullWidth
            >
              下载 Windows 版本
            </Button>

            {/* Mac 版本选择 */}
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                startIcon={<DownloadIcon />}
                href="/adb-tool/downloads/adb-agent-mac-intel"
                download
                onClick={() => setPolling(true)}
                fullWidth
              >
                Mac Intel 版本
              </Button>
              <Button
                variant="contained"
                startIcon={<DownloadIcon />}
                href="/adb-tool/downloads/adb-agent-mac-arm64"
                download
                onClick={() => setPolling(true)}
                fullWidth
              >
                Mac Apple Silicon 版本
              </Button>
            </Box>
          </Box>

          <Alert severity="info">
            <AlertTitle>使用说明</AlertTitle>
            <Typography variant="body2" component="div">
              <ol style={{ margin: 0, paddingLeft: 20 }}>
                <li>点击上方按钮下载对应系统的代理程序</li>
                <li>双击运行下载的文件</li>
              </ol>
            </Typography>
          </Alert>

          <Alert severity="info" sx={{ mt: 2 }}>
            <AlertTitle>Mac 用户如何选择版本？</AlertTitle>
            <Typography variant="body2" component="div">
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li><strong>Intel 版本</strong>：适用于 Intel 芯片的 Mac</li>
                <li><strong>Apple Silicon 版本</strong>：适用于 M1/M2/M3 芯片的 Mac</li>
              </ul>
              <Typography variant="body2" sx={{ mt: 1 }}>
                💡 查看芯片类型：点击左上角  &gt; "关于本机"
              </Typography>
            </Typography>
          </Alert>

          {polling && (
            <Alert severity="success" sx={{ mt: 2 }}>
              <Box display="flex" alignItems="center" gap={1}>
                <CircularProgress size={20} />
                <Typography variant="body2">
                  正在检测代理程序，请运行下载的文件...
                </Typography>
              </Box>
            </Alert>
          )}

          <Box mt={2} textAlign="center">
            <Button onClick={checkAgentAndUpdate} variant="outlined">
              我已运行代理，立即检测
            </Button>
          </Box>
        </Box>
      </Box>
    );
  }

  // 强制更新对话框
  if (updateRequired && updateInfo) {
    return (
      <>
        {/* 半透明遮罩层 */}
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 9998,
          }}
        />
        
        {/* 强制更新对话框 */}
        <Dialog
          open={true}
          disableEscapeKeyDown
          maxWidth="sm"
          fullWidth
          sx={{ zIndex: 9999 }}
        >
          <DialogTitle>
            <Box display="flex" alignItems="center">
              <UpdateIcon sx={{ mr: 1, color: 'primary.main' }} />
              发现新版本
            </Box>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body1" gutterBottom>
                检测到代理程序有新版本，需要更新后才能继续使用。
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                当前版本：{updateInfo.currentVersion || '未知'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                最新版本：{updateInfo.version}
              </Typography>
            </Box>

            {updateInfo.changelog && (
              <Box sx={{ mb: 2, p: 2, backgroundColor: 'grey.100', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  更新内容：
                </Typography>
                <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                  {updateInfo.changelog}
                </Typography>
              </Box>
            )}

            {downloading && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
                  正在下载更新...
                </Typography>
              </Box>
            )}

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>更新步骤：</strong>
              </Typography>
              <Typography variant="body2" component="ol" sx={{ m: 0, pl: 2 }}>
                <li>点击下方"下载更新"按钮</li>
                <li>下载完成后点击"开始安装"</li>
                <li>关闭当前运行的旧版本代理</li>
                <li>运行下载的新文件</li>
                <li>刷新此页面</li>
              </Typography>
            </Alert>

            {downloaded && (
              <>
                <Alert severity="warning" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    <strong>重要提示：</strong>
                  </Typography>
                  <Typography variant="body2">
                    • Windows 可能会提示"是否保留此应用"，请选择<strong>"保留"</strong>
                  </Typography>
                  <Typography variant="body2">
                    • 下载的文件通常在"下载"文件夹中
                  </Typography>
                  <Typography variant="body2">
                    • 安装前请先关闭旧版本代理
                  </Typography>
                </Alert>

                {polling && (
                  <Alert severity="success" sx={{ mt: 2 }}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <CircularProgress size={20} />
                      <Typography variant="body2">
                        正在检测新版本代理，运行后页面将自动刷新...
                      </Typography>
                    </Box>
                  </Alert>
                )}
              </>
            )}
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2, flexDirection: 'column', gap: 1 }}>
            {!downloaded ? (
              <Button
                variant="contained"
                startIcon={downloading ? <CircularProgress size={20} /> : <DownloadIcon />}
                onClick={handleDownloadUpdate}
                disabled={downloading}
                fullWidth
                size="large"
              >
                {downloading ? '正在下载...' : '下载更新'}
              </Button>
            ) : (
              <>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<UpdateIcon />}
                  onClick={handleInstall}
                  fullWidth
                  size="large"
                >
                  开始安装
                </Button>
                <Button
                  variant="outlined"
                  onClick={handleDownloadUpdate}
                  fullWidth
                  size="small"
                >
                  重新下载
                </Button>
              </>
            )}
          </DialogActions>
        </Dialog>
      </>
    );
  }

  // 代理正常运行且版本正确
  return <>{children}</>;
};
