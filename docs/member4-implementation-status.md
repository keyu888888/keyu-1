# 成员4执行链实现状态

## 已跑通

- `scene_spec.json` 的 Pydantic 与 JSON Schema 双重校验；
- SAM 3D 执行边界及真实缓存资产回退；
- Depth Anything 执行边界及三层程序化背景回退；
- GLB、OBJ、PLY 三种资产导入入口；
- 三维资产自动归一化、落地与居中；
- Blender Eevee 自动建场、灯光与背景层；
- `arc_push` 弧线推进；
- `linear_dolly` 直线推拉；
- 首帧、中间帧、末帧的主体安全画框检查；
- 场景预览图和相机路径图；
- 4秒、1280×720、24fps白模视频；
- FFmpeg固定20秒成片模板；
- H.264、`yuv420p`、24fps和480帧输出校验；
- 单入口本地流水线及 `status.json` 状态更新。

## 本地真实验证结果

开发夹具使用 SAM 3D 仓库随附的真实 GLB。弧线推进与直线推拉均已在 Blender 4.5.14 LTS 中执行。

SAM 3D 源码、模型权重及示例资产属于本地可选依赖，不提交到团队 Git 仓库。全新克隆后若未安装该依赖，相关集成测试会自动跳过，基础接口契约测试不受影响。

直线推拉第一次末帧越过底部安全线，被规则自动判为失败；参数收缩后，首、中、尾三帧全部通过，末帧底部安全边距为约3.51%。这验证了安全检查能够阻止不合格镜头进入后续付费生成环节。

白模视频探测结果：

```text
编码 H.264
分辨率 1280×720
像素格式 yuv420p
帧率 24fps
帧数 96
时长 4.000秒
```

固定成片探测结果：

```text
编码 H.264
分辨率 1280×720
像素格式 yuv420p
帧率 24fps
帧数 480
时长 20.000秒
```

## 当前明确使用的降级

- SAM 3D GPU未连接时，读取已验证的真实缓存资产；
- Depth Anything未连接时，使用三层程序化背景；
- 外部视频生成API未配置时，开发夹具以白模视频代替核心生成镜头；
- 比赛演示不得把以上开发降级描述为实时模型推理。

## GPU到位后的替换点

只需替换 `backend/adapters/sam3d_runner.py` 与 `backend/adapters/depth_runner.py` 的执行实现。Blender、镜头、安全检查、FFmpeg和前端产物路径无需改动。

## 常用命令

激活环境不是必需的，可以直接调用虚拟环境解释器：

```powershell
$env:PYTHONPATH='D:\挑战杯'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

复用已渲染白模并运行本地流水线：

```powershell
$env:PYTHONPATH='D:\挑战杯'
.\.venv\Scripts\python.exe -m backend.pipeline.orchestrator --spec tasks/dev_fixture_001/scene_spec.json
```

强制重新渲染完整白模：

```powershell
$env:PYTHONPATH='D:\挑战杯'
.\.venv\Scripts\python.exe -m backend.pipeline.orchestrator --spec tasks/dev_fixture_001/scene_spec.json --no-reuse
```
