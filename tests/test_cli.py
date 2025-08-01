# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

import subprocess

import pytest
from PIL import Image

from tests import CUDA_DEVICE_COUNT, CUDA_IS_AVAILABLE, MODELS, TASK_MODEL_DATA
from ultralytics.utils import ARM64, ASSETS, LINUX, WEIGHTS_DIR, checks
from ultralytics.utils.torch_utils import TORCH_1_9


def run(cmd: str) -> None:
    """Execute a shell command using subprocess."""
    subprocess.run(cmd.split(), check=True)


def test_special_modes() -> None:
    """Test various special command-line modes for YOLO functionality."""
    run("yolo help")
    run("yolo checks")
    run("yolo version")
    run("yolo settings reset")
    run("yolo cfg")


@pytest.mark.parametrize("task,model,data", TASK_MODEL_DATA)
def test_train(task: str, model: str, data: str) -> None:
    """Test YOLO training for different tasks, models, and datasets."""
    run(f"yolo train {task} model={model} data={data} imgsz=32 epochs=1 cache=disk")


@pytest.mark.parametrize("task,model,data", TASK_MODEL_DATA)
def test_val(task: str, model: str, data: str) -> None:
    """Test YOLO validation process for specified task, model, and data using a shell command."""
    run(f"yolo val {task} model={model} data={data} imgsz=32 save_txt save_json")


@pytest.mark.parametrize("task,model,data", TASK_MODEL_DATA)
def test_predict(task: str, model: str, data: str) -> None:
    """Test YOLO prediction on provided sample assets for specified task and model."""
    run(f"yolo {task} predict model={model} source={ASSETS} imgsz=32 save save_crop save_txt visualize")


@pytest.mark.parametrize("model", MODELS)
def test_export(model: str) -> None:
    """Test exporting a YOLO model to TorchScript format."""
    run(f"yolo export model={model} format=torchscript imgsz=32")


def test_rtdetr(task: str = "detect", model: str = "yolov8n-rtdetr.yaml", data: str = "coco8.yaml") -> None:
    """Test the RTDETR functionality within Ultralytics for detection tasks using specified model and data."""
    # Warning: must use imgsz=640 (note also add comma, spaces, fraction=0.25 args to test single-image training)
    run(f"yolo train {task} model={model} data={data} --imgsz= 160 epochs =1, cache = disk fraction=0.25")  # spaces
    run(f"yolo predict {task} model={model} source={ASSETS / 'bus.jpg'} imgsz=160 save save_crop save_txt")
    if TORCH_1_9:
        weights = WEIGHTS_DIR / "rtdetr-l.pt"
        run(f"yolo predict {task} model={weights} source={ASSETS / 'bus.jpg'} imgsz=160 save save_crop save_txt")
        run(f"yolo train {task} model={weights} epochs=1 imgsz=160 cache=disk data=coco8.yaml")


@pytest.mark.skipif(checks.IS_PYTHON_3_12, reason="MobileSAM with CLIP is not supported in Python 3.12")
@pytest.mark.skipif(
    checks.IS_PYTHON_3_8 and LINUX and ARM64,
    reason="MobileSAM with CLIP is not supported in Python 3.8 and aarch64 Linux",
)
def test_fastsam(
    task: str = "segment", model: str = WEIGHTS_DIR / "FastSAM-s.pt", data: str = "coco8-seg.yaml"
) -> None:
    """Test FastSAM model for segmenting objects in images using various prompts within Ultralytics."""
    source = ASSETS / "bus.jpg"

    run(f"yolo segment val {task} model={model} data={data} imgsz=32")
    run(f"yolo segment predict model={model} source={source} imgsz=32 save save_crop save_txt")

    from ultralytics import FastSAM
    from ultralytics.models.sam import Predictor

    # Create a FastSAM model
    sam_model = FastSAM(model)  # or FastSAM-x.pt

    # Run inference on an image
    for s in (source, Image.open(source)):
        everything_results = sam_model(s, device="cpu", retina_masks=True, imgsz=320, conf=0.4, iou=0.9)

        # Remove small regions
        new_masks, _ = Predictor.remove_small_regions(everything_results[0].masks.data, min_area=20)

        # Run inference with bboxes and points and texts prompt at the same time
        sam_model(source, bboxes=[439, 437, 524, 709], points=[[200, 200]], labels=[1], texts="a photo of a dog")


def test_mobilesam() -> None:
    """Test MobileSAM segmentation with point prompts using Ultralytics."""
    from ultralytics import SAM

    # Load the model
    model = SAM(WEIGHTS_DIR / "mobile_sam.pt")

    # Source
    source = ASSETS / "zidane.jpg"

    # Predict a segment based on a 1D point prompt and 1D labels.
    model.predict(source, points=[900, 370], labels=[1])

    # Predict a segment based on 3D points and 2D labels (multiple points per object).
    model.predict(source, points=[[[900, 370], [1000, 100]]], labels=[[1, 1]])

    # Predict a segment based on a box prompt
    model.predict(source, bboxes=[439, 437, 524, 709], save=True)

    # Predict all
    # model(source)


# Slow Tests -----------------------------------------------------------------------------------------------------------
@pytest.mark.slow
@pytest.mark.parametrize("task,model,data", TASK_MODEL_DATA)
@pytest.mark.skipif(not CUDA_IS_AVAILABLE, reason="CUDA is not available")
@pytest.mark.skipif(CUDA_DEVICE_COUNT < 2, reason="DDP is not available")
def test_train_gpu(task: str, model: str, data: str) -> None:
    """Test YOLO training on GPU(s) for various tasks and models."""
    run(f"yolo train {task} model={model} data={data} imgsz=32 epochs=1 device=0")  # single GPU
    run(f"yolo train {task} model={model} data={data} imgsz=32 epochs=1 device=0,1")  # multi GPU


@pytest.mark.parametrize(
    "solution",
    ["count", "blur", "workout", "heatmap", "isegment", "visioneye", "speed", "queue", "analytics", "trackzone"],
)
def test_solutions(solution: str) -> None:
    """Test yolo solutions command-line modes."""
    run(f"yolo solutions {solution} verbose=False")
