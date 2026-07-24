param()
$E = [char]27
$R = "$E[0m"
$g  = "$E[93m"
$c  = "$E[36m"
$g2 = "$E[32m"
$b  = "$E[34m"
$m  = "$E[38;5;208m"
$y  = "$E[33m"

# 读取 stdin - 多策略兼容
$j = ""
try { $j = [Console]::In.ReadToEnd() } catch {}
if (-not $j) { try { $j = @($input) -join '' } catch {} }
$j = $j.Trim()
if (-not $j) { "$g" + "Bing No.1" + "$R"; exit 0 }

try { $d = $j | ConvertFrom-Json } catch { "$g" + "Bing No.1" + "$R"; exit 0 }

# 清理 [Nm] / [N;Nm]
function c($s) {
    if (-not $s) { return "" }
    return ($s -replace '\[[0-9;]*[a-zA-Z]\]?', '').Trim()
}

$model = $(if ($d.model.display_name) { c $d.model.display_name } else { "?" })

# Git 分支
$branch = "?"
try { $gitOut = & git -C "$($d.workspace.current_dir)" branch --show-current 2>$null; if ($gitOut) { $branch = $gitOut.Trim() } } catch {}

# Context
$ctx = "?"
if ($d.context_window.used_percentage -ne $null) {
    $p = $d.context_window.used_percentage
    $ctx = if ($p -eq [int]$p) { "$p%" } else { "{0:N1}%" -f $p }
}

# Token
$cu = $d.context_window.current_usage
$in = 0; $out = 0; $cache = 0; $total = 0
if ($cu) {
    $in    = if ($cu.input_tokens -ne $null)    { $cu.input_tokens } else { 0 }
    $out   = if ($cu.output_tokens -ne $null)   { $cu.output_tokens } else { 0 }
    $cache = if ($cu.cache_read_input_tokens -ne $null) { $cu.cache_read_input_tokens } elseif ($cu.cache_creation_input_tokens -ne $null) { $cu.cache_creation_input_tokens } else { 0 }
    $total = $in + $out + $cache
}

function f($n) {
    if ($n -ge 1000000) { return "{0:N1}M" -f ($n / 1000000) }
    if ($n -ge 1000)    { return "{0:N0}K" -f ($n / 1000) }
    return "$n"
}

$tok = "?"
if ($total -gt 0) {
    $dd = @(); $dd += "in:" + (f $in); $dd += "out:" + (f $out)
    if ($cache -gt 0) { $dd += "cache:" + (f $cache) }
    $tok = "Tokens $(f $total)($($dd -join ','))"
}

# 时长
$dur = "?"
if ($d.cost.total_duration_ms -ne $null) {
    $ts = [math]::Floor($d.cost.total_duration_ms / 1000)
    $hh = [math]::Floor($ts / 3600); $mm = [math]::Floor(($ts % 3600) / 60); $ss = $ts % 60
    $dur = if ($hh -gt 0) { "${hh}h ${mm}m" } elseif ($mm -gt 0) { "${mm}m ${ss}s" } else { "${ss}s" }
}

$out = ""
$out = $out + $c + $model + $R
$out = $out + " | "
$out = $out + $g2 + "git:($branch)" + $R
$out = $out + " | "
$out = $out + $b + "Context:$ctx" + $R
$out = $out + " | "
$out = $out + $y + $dur + $R
$out = $out + " | "
$out = $out + $g + "Bing No.1" + $R
$out = $out + "`n"
$out = $out + $m + $tok + $R
$out
