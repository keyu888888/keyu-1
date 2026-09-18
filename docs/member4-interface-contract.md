# 成员4执行链接口契约 v0.1

## 输入

成员4的工具只接收经过 Schema 校验的 `scene_spec.json` 和任务目录。所有相对路径均以项目根目录为基准，禁止传入任意 Python 或 Blender 表达式。

最小输入字段如下：

| 字段 | 类型 | 说明 |
|---|---|---|
| `job_id` | string | 任务唯一标识 |
| `hero_image` | string | 主视觉原图路径 |
| `reconstruction_budget` | integer | 10天版固定为1 |
| `targets` | array | 目标、掩膜、表示方式和可选缓存资产 |
| `background` | object | 深度图与2至3层背景参数 |
| `camera` | object | 仅允许 `linear_dolly` 或 `arc_push` |
| `render` | object | 10天版固定为720p、24fps、4至6秒 |
| `generation` | object | 视频平台、提示词和缓存策略 |
| `edit` | object | 固定成片时长、标题、音乐和输出路径 |

## 四个工具

### reconstruct_object

输入：原图、掩膜、目标ID、输出目录。

输出：三维资产、元数据、耗时；失败时返回代理建议，不抛出未经处理的异常。

### build_blender_scene

输入：`scene_spec.json`、已存在的三维或代理资产、深度/背景层。

输出：场景文件、预览图、相机路径图、首中尾检查帧和白模视频。

### generate_core_video

输入：主图、白模视频、受限提示词、生成参数。

输出：平台任务ID、核心视频和请求记录；API失败时允许返回最近一次真实缓存。

### compose_final_video

输入：照片列表、核心视频、标题、音乐和固定剪辑模板。

输出：H.264、yuv420p、AAC的横屏720p成片。

## 统一返回值

每个工具必须返回 `backend/contracts/tool_result.schema.json` 定义的对象。成员2根据返回值统一更新状态文件。

成员4不得直接并发写入 `status.json`，避免与总流程发生覆盖。

## 错误码

| 错误码 | 含义 | 是否可重试 | 默认回退 |
|---|---|---|---|
| `E401_MASK_INVALID` | 掩膜无效 | 是 | 修正掩膜或更换对象 |
| `E402_SAM3D_FAILED` | 对象重建失败 | 是 | 使用缓存资产或代理 |
| `E403_ASSET_IMPORT_FAILED` | Blender资产导入失败 | 是 | 转换格式或使用代理 |
| `E404_SCENE_BUILD_FAILED` | 场景构建失败 | 是 | 减少场景元素 |
| `E405_CAMERA_UNSAFE` | 镜头安全检查失败 | 是 | 幅度乘0.7，再退回直线推拉 |
| `E406_RENDER_FAILED` | 白模渲染失败 | 是 | 降分辨率并保留场景 |
| `E407_VIDEO_API_FAILED` | 视频接口失败 | 是 | 只重试接口或读取真实缓存 |
| `E408_COMPOSE_FAILED` | 最终剪辑失败 | 是 | 标准化媒体后重试 |

## 版本规则

- 当前契约版本为 `0.1.0`。
- 第2天开始，删除或重命名字段必须经成员1、2、3、4共同确认。
- 新增可选字段不得破坏已有样例任务。

