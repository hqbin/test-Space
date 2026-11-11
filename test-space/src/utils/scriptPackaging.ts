/**
 * 脚本打包：把编辑器里的源码转成「能独立运行」的最终文件字节。
 *
 * 背景：过去「应用内运行」和「导出为文件」是两条各自写盘的链路——
 * 运行由 Rust 侧补 CRLF、由 cmd 前缀补 chcp 65001，导出则原样落盘。
 * 同一份 BAT 在应用里能跑、导出后双击报错，用户只能归因到「导出坏了」。
 *
 * 现在两条链路都调用 packageScript()，产物字节完全一致；每处改动都通过
 * changes 上抛，由界面如实展示，不再有隐式加工。
 *
 * 处理范围刻意收得很窄——只做「不改就不是同一个程序」的两件事：
 *   1. echo 行里的 -> / => 会被 cmd 当重定向，必须中性化；
 *   2. 含非 ASCII 却缺 chcp 65001 时，cmd 默认 GBK 会把 UTF-8 中文拆成命令。
 * 全角标点、缩进、大小写一律不动：在 chcp 65001 下它们本来就能正常显示，
 * 擅自改成半角只会改掉用户 echo 出来的文案。
 */

export type ScriptType = "bat" | "py";

/** 打包过程中实际做过的修改，用于在界面上如实告知用户 */
export type PackagingChange = "arrow" | "codepage" | "crlf";

export interface PackagedScript {
  /** 最终写入磁盘的内容（BAT 为 UTF-8 + CRLF） */
  content: string;
  /** 相对编辑器内容发生的改动；空数组表示原样输出 */
  changes: PackagingChange[];
}

/** `echo A -> B` 里的 `>` 会被当成重定向，`=>` 同理 */
const ARROW_MAP: [RegExp, string][] = [
  [/->/g, " to "],
  [/=>/g, " to "],
];

const CHCP_UTF8_RE = /^\s*(?:@)?chcp\s+65001\b/im;
const NON_ASCII_RE = /[^\x00-\x7F]/;

/**
 * 中性化 echo 行里会被 cmd 误当重定向的箭头写法。
 * 只处理 echo（rem / :: 不执行，改了反而破坏注释内容），输入输出均为 LF。
 */
export function neutralizeEchoRedirection(code: string): string {
  return code
    .split("\n")
    .map(line => {
      if (!/^\s*echo\b/i.test(line)) return line;
      let result = line;
      for (const [pattern, replacement] of ARROW_MAP) {
        result = result.replace(pattern, replacement);
      }
      return result;
    })
    .join("\n");
}

/**
 * 判断这份 BAT 在打包时是否需要补 chcp 65001。
 * 纯 ASCII 脚本与代码页无关，保持原样，避免无谓改动。
 */
export function needsUtf8Codepage(code: string): boolean {
  if (!NON_ASCII_RE.test(code)) return false;
  if (CHCP_UTF8_RE.test(code)) return false;
  return true;
}

/**
 * 含中文的 BAT 若缺 chcp，插到 @echo off 之后（没有则放首行），
 * 保证在默认 GBK 的 cmd 里也能正确解析 UTF-8 中文。
 * 只加一行、不改任何原有语句，且会体现在 changes 里。
 */
function ensureUtf8Codepage(code: string): { code: string; injected: boolean } {
  if (!needsUtf8Codepage(code)) return { code, injected: false };

  const lines = code.split("\n");
  const echoOffIdx = lines.findIndex(l => /^\s*@?echo\s+off\s*$/i.test(l));
  const chcpLine = "chcp 65001 >nul";

  if (echoOffIdx !== -1) {
    lines.splice(echoOffIdx + 1, 0, chcpLine);
  } else {
    lines.unshift(chcpLine);
  }
  return { code: lines.join("\n"), injected: true };
}

/** cmd.exe 的括号块 / goto 标签对 LF 敏感，统一成 CRLF */
function toCrlf(code: string): { code: string; changed: boolean } {
  if (!code.includes("\n")) return { code, changed: false };
  return { code: code.replace(/\n/g, "\r\n"), changed: true };
}

/**
 * 运行与导出唯一的产物出口。
 * Python 原样返回（编码与换行交给解释器），BAT 依次做：
 * 换行归一 → echo 箭头中性化 → 补 chcp → CRLF。
 */
export function packageScript(content: string, type: ScriptType): PackagedScript {
  if (type !== "bat") return { content, changes: [] };

  const changes: PackagingChange[] = [];
  let code = content.replace(/\r\n/g, "\n").replace(/\r/g, "\n");

  const neutralized = neutralizeEchoRedirection(code);
  if (neutralized !== code) {
    changes.push("arrow");
    code = neutralized;
  }

  const codepage = ensureUtf8Codepage(code);
  if (codepage.injected) {
    changes.push("codepage");
    code = codepage.code;
  }

  const crlf = toCrlf(code);
  if (crlf.changed) {
    changes.push("crlf");
    code = crlf.code;
  }

  return { content: code, changes };
}
