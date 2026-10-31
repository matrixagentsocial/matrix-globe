# Demo video

`build.py` builds `build/matrix-globe-demo.mp4` (about 2:20, 1920x1080) from
[`docs/video-script.md`](../docs/video-script.md), version B (Matrix offline).

- **Voice:** [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) (open weights,
  Apache 2.0), voice `af_heart`, run locally through `kokoro-onnx`. No human voice.
- **Footage:** Playwright records the real public pages (the proof viewer, the
  repository and its `sandbox` Actions runs). The terminal cards replay the
  real output of the desk dry run in `docs/desk-dry-run-open-gha.md`.
- **Numbers:** every number on a card is read from `results/` at build time.
- **Captions:** burned in from the narration lines (`build/captions.ass`).

Tools (outside the project venv):

```bash
python -m venv vtools && vtools/Scripts/pip install kokoro-onnx soundfile playwright
vtools/Scripts/python -m playwright install chromium
gh release download model-files-v1.0 -R thewh1teagle/kokoro-onnx -p kokoro-v1.0.onnx -p voices-v1.0.bin -D models
vtools/Scripts/python video/build.py --models models
```

`ffmpeg` must be on PATH. `--only tts|record|assemble` and `--shots a,b` redo one step.
