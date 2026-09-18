# Re Dream 挑战杯原型

本仓库保存 Re Dream 手机散片自动成片 Agent 的方案文档，以及成员4负责的三维场景、镜头规划、白模安全检查和视频合成原型代码。

## 当前完成情况

- 已定义 `scene_spec` 与工具返回值的接口契约；
- 已实现 SAM 3D、Depth Anything 的调用边界与无 GPU 降级路径；
- 已实现 Blender 自动建场、资产归一化、两类镜头模板和主体安全画框检查；
- 已实现白模渲染、FFmpeg 20 秒成片模板与本地单入口流水线；
- 已在本机用真实缓存 GLB 跑通 1280×720、24fps 的开发夹具。

当前演示使用缓存三维资产和程序化景深背景，不代表 SAM 3D 或 Depth Anything 已完成实时 GPU 推理。详细状态见 [`docs/member4-implementation-status.md`](docs/member4-implementation-status.md)。

## 快速验证

推荐 Python 3.11：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-member4-dev.txt
$env:PYTHONPATH=(Get-Location).Path
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\validate_contracts.py
```

运行本地开发夹具前，还需按下文准备 Blender、FFmpeg 和可选的 SAM 3D 示例资产：

```powershell
$env:PYTHONPATH=(Get-Location).Path
.\.venv\Scripts\python.exe -m backend.pipeline.orchestrator --spec tasks/dev_fixture_001/scene_spec.json
```

## 本地依赖与大文件

以下内容不会进入 Git：模型权重、第三方 `sam-3d-objects-main` 源码目录、Python 虚拟环境、便携版 Blender/FFmpeg、三维模型、渲染图和生成视频。这样可以避免泄露凭证，也不会让仓库被大文件拖垮。

本机开发时：

1. 将官方 SAM 3D Objects 源码放在仓库根目录的 `sam-3d-objects-main/`；
2. 将 Blender 和 FFmpeg 放入 `.env.example` 所示位置，或通过环境变量指定可执行文件；
3. 权重和访问令牌只保存在本机，不要提交 `.env`。

缺少这些可选本地资产时，基础契约测试仍可执行，依赖 SAM 示例资产的集成测试会自动跳过。

## 目录说明

- `backend/schemas/`：Python 数据模型；
- `backend/contracts/`：跨成员使用的 JSON Schema 与示例；
- `backend/adapters/`：SAM 3D、深度估计、Blender、视频生成适配层；
- `backend/blender_scripts/`：自动建场、镜头模板与安全检查；
- `backend/pipeline/`：本地流水线与成片合成；
- `tasks/`：仅提交任务规格和状态骨架，不提交生成产物；
- `docs/`：成员4接口、实施状态和阶段报告。

## 团队协作

按 [`Git与Overleaf团队协作教程.md`](Git与Overleaf团队协作教程.md) 操作：功能代码先提交至成员自己的 `feature/...` 分支，再通过 Pull Request 合并到 `develop`，不要直接向主分支推送。
