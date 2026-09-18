# 成员4第一天环境与接口冻结记录

## 当日结论

成员4的10天 Demo 关键路径冻结为：单对象或代理资产、背景深度、Blender 自动建场、直线推拉与弧线推进、白模安全预览、一个视频生成适配器、FFmpeg 固定模板成片。

10天版不把多对象自动重建、人物三维、小角度环绕、遮挡横移、自由时间线和自动卡点放入关键路径。

## 2026年9月18日本机环境盘点

| 项目 | 状态 | 影响 | 处理 |
|---|---|---|---|
| Git | 已安装 | 可进行版本管理 | 需要团队成员在本人账户下执行 `git init`；沙箱账户存在目录所有权限制 |
| Python | 已安装并验证 | 项目内便携 Python 3.11.9，含 pip 和 venv | 10天原型使用该环境；Linux部署可继续使用方案指定的3.11.16 |
| Conda 或 Mamba | 未安装 | 无法创建 SAM 3D 独立环境 | SAM 3D 应部署到 Linux GPU 服务器，不建议塞入本机 Web 环境 |
| FFmpeg 与 FFprobe | 已安装并验证 | 项目内便携 FFmpeg 9.0.1 | 已通过 H.264、yuv420p、24fps 编码和探测测试 |
| Blender | 已安装并验证 | 项目内便携 Blender 4.5.14 LTS | 已通过后台模式和 Eevee 实际渲染测试 |
| NVIDIA 工具 | 未检测到 | 本机无法确认有可用 NVIDIA GPU | 需要提供远程 Linux GPU，或采用真实结果缓存 |
| WSL | 未完成安装 | 本机暂无可用 Linux 环境 | 不把 WSL 安装作为10天 Demo 的 SAM 3D 主路径 |
| SAM 3D 权重 | 缺失 | 本地仓库不能直接推理 | 申请 Hugging Face 权限并在远程 GPU 下载 |

便携工具位于 `tools/`，该目录已经加入 `.gitignore`，不随代码仓库提交。Python 3.11.16 官方在 Windows 端仅发布源码，因此本机原型采用同一功能版本线的 Python 3.11.9；这不会影响当前 Blender、FFmpeg 与接口开发。

项目虚拟环境 `.venv` 已创建，并安装 Pydantic 2.12.4 与 jsonschema 4.26.0。`scene_spec.json` 和统一工具返回值样例均已通过 Draft 2020-12 Schema 校验。

## 已冻结的职责边界

- 成员1负责决定主图、目标对象、镜头模板和叙事参数，并生成符合契约的 `scene_spec.json`。
- 成员2负责总流程、状态机和唯一写入 `status.json`。
- 成员3只消费 `status.json` 与产物路径，不直接调用 Blender、SAM 3D 或视频平台。
- 成员4实现执行工具，返回统一的 `tool_result`，不得绕过契约解析自然语言。
- 成员5负责素材授权、测试记录、耗时、费用、失败次数和演示资料。

## 成员4第2天进入条件

以下条件至少满足一条：

1. 获得 Linux 64 位、NVIDIA GPU 且显存建议不低于 32GB 的服务器，并取得 SAM 3D 权重访问权限；
2. 团队提供已经由真实 SAM 3D 生成的 `.ply` 或 `.glb` 资产及其输入图、掩膜和运行记录，用于先完成 Blender 执行链。

无论 SAM 3D 是否就绪，Blender 和 FFmpeg 安装完成后都可并行推进建场、运镜和成片。第2天18点仍未获得 GPU 或权重时，关键路径自动切换为“真实预计算资产加代理降级”，不再等待。

## 演示素材要求

需要团队提供一组自有或明确授权的主演示照片，共3至6张。建议选择校园建筑或桌面静物：主体轮廓完整，存在前中后景，避免玻璃、镜面、密集树叶、多人遮挡和复杂毛发。

## 复查命令

在 PowerShell 中运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_member4_env.ps1
```

当前 Python、FFmpeg、FFprobe 和 Blender 已为 `available=true`。SAM 3D 的 GPU与权重仍需在远程 Linux 环境单独检查。
