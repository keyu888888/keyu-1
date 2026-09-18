from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class VideoGenerator(ABC):
    @abstractmethod
    def submit(
        self,
        image_path: Path,
        control_video_path: Path,
        prompt: str,
        options: dict[str, Any],
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def poll(self, task_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def download(self, task_id: str, output_path: Path) -> Path:
        raise NotImplementedError


class UnconfiguredVideoGenerator(VideoGenerator):
    def submit(self, image_path: Path, control_video_path: Path, prompt: str, options: dict[str, Any]) -> str:
        raise RuntimeError("Video generation API is not configured")

    def poll(self, task_id: str) -> dict[str, Any]:
        raise RuntimeError("Video generation API is not configured")

    def download(self, task_id: str, output_path: Path) -> Path:
        raise RuntimeError("Video generation API is not configured")

