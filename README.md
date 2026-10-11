# Windows 创建快捷方式（COM 被封时的可行通道）

在受限环境（COM 组件被安全策略拦截）下创建 Windows 桌面快捷方式的可行通道：拿系统原生 .lnk 做母本，按 LNK 二进制格式补丁参数区，再用 ctypes 走外壳解析器验证结果可用。

How to create Windows shortcuts when COM automation is blocked by security policy: patch the binary format of a native .lnk in place, then verify through the shell resolver via ctypes. Includes the patch and verify scripts.

完整手册 / Full manual: [SKILL.md](SKILL.md)

---

*实测干货技能，作者与 AI 代理日常打磨而成 / A battle-tested skill, refined daily with AI agents.*
