from __future__ import annotations

import json
from pathlib import Path
import unittest

from backend.schemas import SceneSpec, ToolResult
from backend.adapters.sam3d_runner import reconstruct_object
from backend.adapters.depth_runner import estimate_depth


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAM_FIXTURE_ROOT = PROJECT_ROOT / "sam-3d-objects-main/notebook"
SAM_FIXTURE_IMAGE = SAM_FIXTURE_ROOT / "images/shutterstock_stylish_kidsroom_1640806567/image.png"
SAM_FIXTURE_MASK = SAM_FIXTURE_ROOT / "images/shutterstock_stylish_kidsroom_1640806567/14.png"
SAM_FIXTURE_ASSET = SAM_FIXTURE_ROOT / "meshes/human_object/3Dfy_results/0.glb"


class ContractTests(unittest.TestCase):
    def test_demo_scene_spec(self) -> None:
        data = json.loads((PROJECT_ROOT / "tasks/demo_001/scene_spec.json").read_text(encoding="utf-8"))
        model = SceneSpec.model_validate(data)
        self.assertEqual(model.contract_version, "0.1.0")
        self.assertLessEqual(model.reconstruction_budget, 1)

    def test_development_fixture_spec(self) -> None:
        data = json.loads((PROJECT_ROOT / "tasks/dev_fixture_001/scene_spec.json").read_text(encoding="utf-8"))
        model = SceneSpec.model_validate(data)
        self.assertEqual(model.camera.template, "arc_push")

    def test_tool_result_example(self) -> None:
        payload = (PROJECT_ROOT / "backend/contracts/examples/tool_result.white_model.json").read_text(encoding="utf-8")
        result = ToolResult.model_validate_json(payload)
        self.assertTrue(result.success)

    @unittest.skipUnless(
        SAM_FIXTURE_IMAGE.exists() and SAM_FIXTURE_MASK.exists() and SAM_FIXTURE_ASSET.exists(),
        "可选的 SAM 3D 本地开发夹具未安装",
    )
    def test_sam3d_cached_asset_boundary(self) -> None:
        result = reconstruct_object(
            SAM_FIXTURE_IMAGE,
            SAM_FIXTURE_MASK,
            PROJECT_ROOT / "tasks/dev_fixture_001/assets/object.glb",
            cached_asset=SAM_FIXTURE_ASSET,
        )
        self.assertTrue(result.success)
        self.assertTrue(result.fallback_used)

    @unittest.skipUnless(SAM_FIXTURE_IMAGE.exists(), "可选的 SAM 3D 本地开发夹具未安装")
    def test_depth_procedural_fallback(self) -> None:
        result = estimate_depth(
            SAM_FIXTURE_IMAGE,
            PROJECT_ROOT / "tasks/dev_fixture_001/depth/depth_raw.png",
        )
        self.assertTrue(result.success)
        self.assertTrue(result.fallback_used)


if __name__ == "__main__":
    unittest.main()
