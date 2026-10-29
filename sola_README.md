**# SOLA Setup & Usage Notes**



這份 README 記錄 SOLA 的環境建置與目前桌球影片測試流程。



目前研究流程：



\`\`\`text

MP4

 ↓

Frames

 ↓

GroundingDINO 找候選選手

 ↓

SAM2 產生 Player Tracks / Masks

 ↓

檢查 Tracking 品質

 ↓

如果可用，再訓練 SOLA

 ↓

使用文字選出主要擊球者

\`\`\`



目前硬體 / 環境：



\`\`\`text

Python:        3.10

PyTorch:       2.6.0+cu124

torchvision:   0.21.0

CUDA (Torch):  12.4

System CUDA:   12.6

GPU:           Tesla V100-SXM2-16GB

\`\`\`



**---**



**# Part 1. Environment Setup**



**## 1. Clone SOLA**



\`\`\`bash

cd /home/code-server/cyt

git clone https\://github.com/cvlab-kaist/SOLA.git

cd SOLA

\`\`\`



建立獨立 Conda environment：



\`\`\`bash

conda create -n sola python=3.10 -y

conda activate sola

\`\`\`



確認：



\`\`\`bash

which python

python --version

\`\`\`



應該類似：



\`\`\`text

/opt/conda/envs/sola/bin/python

Python 3.10.x

\`\`\`



**---**



**## 2. Install SOLA Dependencies**



在 SOLA root：



\`\`\`bash

cd /home/code-server/cyt/SOLA

pip install -r requirements.txt

\`\`\`



確認 PyTorch / CUDA：



\`\`\`bash

python - <<'PY'

import torch



print("Torch:", torch.\_\_version\_\_)

print("CUDA:", torch.version.cuda)

print("CUDA available:", torch.cuda.is_available())



if torch.cuda.is_available():

    print("GPU:", torch.cuda.get_device_name(0))

PY

\`\`\`



目前成功結果：



\`\`\`text

Torch: 2.6.0+cu124

CUDA: 12.4

CUDA available: True

GPU: Tesla V100-SXM2-16GB

\`\`\`



注意：



\`\`\`text

System CUDA = 12.6

PyTorch CUDA = 12.4

\`\`\`



編譯 extension 時會出現 minor version mismatch warning，但目前可正常使用。



**---**



**## 3. Install SAM2**



SOLA 要求 SAM2 放在：



\`\`\`text

SOLA/track_generation/sam2_repo

\`\`\`



安裝：



\`\`\`bash

cd /home/code-server/cyt/SOLA/track_generation



git clone https\://github.com/facebookresearch/sam2.git

cd sam2

pip install -e .

\`\`\`



測試：



\`\`\`bash

python - <<'PY'

import sam2

print("SAM2 import OK")

PY

\`\`\`



**---**



**## 4. Download SAM2 Checkpoints**



\`\`\`bash

cd /home/code-server/cyt/SOLA/track_generation/sam2_repo/checkpoints

./download_ckpts.sh

\`\`\`



目前已有：



\`\`\`text

sam2.1_hiera_tiny.pt

sam2.1_hiera_small.pt

sam2.1_hiera_base_plus.pt

sam2.1_hiera_large.pt

\`\`\`



目前 V100 16GB 測試 tracking 時，先使用：



\`\`\`text

sam2.1_hiera_small.pt

\`\`\`



如果效果不足，再測：



\`\`\`text

sam2.1_hiera_base_plus.pt

sam2.1_hiera_large.pt

\`\`\`



**---**



**## 5. Install GroundingDINO**



SOLA 要求 GroundingDINO 放在：



\`\`\`text

SOLA/track_generation/GroundingDINO

\`\`\`



下載：



\`\`\`bash

cd /home/code-server/cyt/SOLA/track_generation



git clone https\://github.com/IDEA-Research/GroundingDINO.git

cd GroundingDINO

\`\`\`



先安裝 ninja：



\`\`\`bash

python -m pip install ninja

\`\`\`



**---**



**## 6. Fix GroundingDINO for PyTorch 2.6**



GroundingDINO 的 CUDA extension 和 PyTorch 2.6 有相容性問題。



檔案：



\`\`\`text

groundingdino/models/GroundingDINO/csrc/MsDeformAttn/ms_deform_attn_cuda.cu

\`\`\`



先查看：



\`\`\`bash

grep -n -E "type\\\\(\\\\)|scalar_type" groundingdino/models/GroundingDINO/csrc/MsDeformAttn/ms_deform_attn_cuda.cu

\`\`\`



正確狀態應類似：



\`\`\`text

35:  value.type().is_cuda()

65:  AT_DISPATCH_FLOATING_TYPES(value.scalar_type(), ...)

101: value.type().is_cuda()

135: AT_DISPATCH_FLOATING_TYPES(value.scalar_type(), ...)

\`\`\`



**### CUDA tensor check**



以下應保持：



\`\`\`cpp

value.type().is_cuda()

\`\`\`



如果不小心變成：



\`\`\`cpp

value.scalar_type().is_cuda()

\`\`\`



會出現：



\`\`\`text

expression must have class type but it has type "c10::ScalarType"

\`\`\`



修正：



\`\`\`bash

sed -i 's/value.scalar_type().is_cuda()/value.type().is_cuda()/g' groundingdino/models/GroundingDINO/csrc/MsDeformAttn/ms_deform_attn_cuda.cu

\`\`\`



**### AT_DISPATCH**



以下：



\`\`\`cpp

AT_DISPATCH_FLOATING_TYPES(value.type(), ...)

\`\`\`



在 PyTorch 2.6 會出現：



\`\`\`text

no suitable conversion function from

"const at::DeprecatedTypeProperties"

to "c10::ScalarType"

\`\`\`



應改成：



\`\`\`cpp

AT_DISPATCH_FLOATING_TYPES(value.scalar_type(), ...)

\`\`\`



也就是 forward / backward 兩個位置都使用：



\`\`\`cpp

value.scalar_type()

\`\`\`



**---**



**## 7. Build GroundingDINO**



不要直接：



\`\`\`bash

pip install -e .

\`\`\`



之前會在 build isolation 裡找不到：



\`\`\`text

torch

pip

\`\`\`



使用：



\`\`\`bash

cd /home/code-server/cyt/SOLA/track_generation/GroundingDINO

python -m pip install -e . --no-build-isolation

\`\`\`



**---**



**## 8. Fix Transformers Version**



GroundingDINO 自動安裝新版 Transformers 5.x 時，曾出現：



\`\`\`text

AttributeError:

'BertModel' object has no attribute 'get_extended_attention_mask'

\`\`\`



目前可用版本：



\`\`\`text

transformers = 4.37.2

tokenizers   = 0.15.2

\`\`\`



修正：



\`\`\`bash

python -m pip uninstall transformers tokenizers -y

python -m pip install "transformers==4.37.2"

\`\`\`



確認：



\`\`\`bash

python - <<'PY'

import transformers

print(transformers.\_\_version\_\_)

PY

\`\`\`



應為：



\`\`\`text

4.37.2

\`\`\`



**---**



**## 9. Fix OpenCV libGL Error**



Server 曾出現：



\`\`\`text

ImportError: libGL.so.1: cannot open shared object file

\`\`\`



改成 headless OpenCV：



\`\`\`bash

python -m pip uninstall opencv-python -y

python -m pip install opencv-python-headless

\`\`\`



確認：



\`\`\`bash

python - <<'PY'

import cv2

print("OpenCV:", cv2.\_\_version\_\_)

PY

\`\`\`



**---**



**## 10. Download GroundingDINO Checkpoint**



\`\`\`bash

cd /home/code-server/cyt/SOLA/track_generation/GroundingDINO



mkdir -p weights

cd weights



wget https\://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth

\`\`\`



目前使用：



\`\`\`text

Config:

groundingdino/config/GroundingDINO_SwinT_OGC.py



Checkpoint:

weights/groundingdino_swint_ogc.pth

\`\`\`



**---**



**## 11. Final Environment Test**



\`\`\`bash

conda activate sola



python - <<'PY'

import torch



print("Torch:", torch.\_\_version\_\_)

print("CUDA:", torch.version.cuda)

print("CUDA available:", torch.cuda.is_available())



if torch.cuda.is_available():

    print("GPU:", torch.cuda.get_device_name(0))



from groundingdino import \_C

print("GroundingDINO CUDA extension OK")



import sam2

print("SAM2 import OK")

PY

\`\`\`



目前成功：



\`\`\`text

Torch: 2.6.0+cu124

CUDA available: True

GPU: Tesla V100-SXM2-16GB

GroundingDINO CUDA extension OK

SAM2 import OK

\`\`\`



注意：



GroundingDINO \`\_C\` 測試時最好先：



\`\`\`python

import torch

\`\`\`



再：



\`\`\`python

from groundingdino import \_C

\`\`\`



否則曾出現：



\`\`\`text

ImportError: libc10.so: cannot open shared object file

\`\`\`



**---**



**# Part 2. Usage**



**## 12. Current Test Data**



目前測試影片：



\`\`\`text

/home/code-server/table_tennis_video/test_samples_10_fixed/test

\`\`\`



包含：



\`\`\`text

461_100.mp4

505_311.mp4

508_443.mp4

622_005.mp4

\`\`\`



**---**



**## 13. Convert MP4 to Frames**



SAM2 / SOLA 後面的 video tracking 使用 frame directory，因此先把 MP4 拆成圖片。



建立：



\`\`\`text

video2frame.sh

\`\`\`



內容：



\`\`\`bash

\#!/bin/bash



INPUT_DIR="/home/code-server/table_tennis_video/test_samples_10_fixed/test"

OUTPUT_DIR="/home/code-server/cyt/sola_track_test/frames"



mkdir -p "$OUTPUT_DIR"



for f in "$INPUT_DIR"/\*.mp4; do

    name=$(basename "$f" .mp4)

    mkdir -p "$OUTPUT_DIR/$name"

    ffmpeg -y -i "$f" -vsync 0 "$OUTPUT_DIR/$name/%05d.jpg"

done

\`\`\`



執行：



\`\`\`bash

cd /home/code-server/cyt/SOLA

bash video2frame.sh

\`\`\`



輸出：



\`\`\`text

/home/code-server/cyt/sola_track_test/frames/

├── 461_100/

├── 505_311/

├── 508_443/

└── 622_005/

\`\`\`



**---**



**## 14. GroundingDINO Prompt Test**



目前目標：



\`\`\`text

GroundingDINO 只負責找出比賽選手候選人

\`\`\`



不是在這一步判斷主要擊球者。



目前測過：



\`\`\`text

person

player

table tennis player

athlete

\`\`\`



觀察結果：



\`\`\`text

person

→ 選手可抓到

→ 裁判也容易被高分抓到

→ 裁判曾約 0.74



player

→ 裁判仍可能被抓

→ 裁判曾約 0.48



table tennis player

→ 比較容易排除裁判

→ 但曾誤抓桌球桌



athlete

→ 目前效果最好

\`\`\`



其中一張 frame：



\`\`\`text

Player A: 0.81

Player B: 0.51

Referee:  0.30

\`\`\`



目前暫定：



\`\`\`text

prompt = athlete

box_threshold = 0.4

text_threshold = 0.25

\`\`\`



**---**



**## 15. Single Frame GroundingDINO Test**



進入：



\`\`\`bash

cd /home/code-server/cyt/SOLA/track_generation/GroundingDINO

\`\`\`



執行：



\`\`\`bash

python demo/inference_on_a_image.py -c groundingdino/config/GroundingDINO_SwinT_OGC.py -p weights/groundingdino_swint_ogc.pth -i /home/code-server/cyt/sola_track_test/frames/505_311/00001.jpg -o output_athlete -t "athlete" --box_threshold 0.4 --text_threshold 0.25

\`\`\`



用來快速看：



\`\`\`text

選手是否都有抓到

裁判是否被抓進來

桌子是否被誤抓

\`\`\`



**---**



**## 16. Batch GroundingDINO Test**



已建立：



\`\`\`text

batch_infer_frames.py

\`\`\`



用途：



\`\`\`text

整個 Frames 資料夾

        ↓

GroundingDINO

        ↓

每張圖找 athlete

        ↓

輸出畫好 bounding box 的圖片

        ↓

detections.csv

\`\`\`



執行：



\`\`\`bash

cd /home/code-server/cyt/SOLA/track_generation/GroundingDINO

\`\`\`



\`\`\`bash

python batch_infer_frames.py \\

  --input_dir /home/code-server/cyt/sola_track_test/frames \\

  --output_dir /home/code-server/cyt/sola_track_test/gdino_athlete_04 \\

  --config groundingdino/config/GroundingDINO_SwinT_OGC.py \\

  --weights weights/groundingdino_swint_ogc.pth \\

  --prompt "athlete" \\

  --box_threshold 0.4 \\

  --text_threshold 0.25 \\

  --recursive

\`\`\`



注意：



\`\`\`text

\--input_dir

\`\`\`



一定要是：



\`\`\`text

/home/code-server/cyt/sola_track_test/frames

\`\`\`



不要填：



\`\`\`text

/home/code-server/table_tennis_video/test_samples_10_fixed/test

\`\`\`



因為後者只有 MP4，\`batch_infer_frames.py\` 只讀圖片，會出現：



\`\`\`text

Found 0 images

\`\`\`



**---**



**## 17. Batch Output**



輸出：



\`\`\`text

/home/code-server/cyt/sola_track_test/gdino_athlete_04/

├── detections.csv

├── 461_100/

├── 505_311/

├── 508_443/

└── 622_005/

\`\`\`



每張圖可以人工檢查：



\`\`\`text

1\. 選手有沒有漏掉

2\. 裁判有沒有被抓到

3\. 桌子有沒有被誤抓

4\. Confidence 是否穩定

5\. 哪些 frame 適合做 SAM2 initialization

\`\`\`



**---**



**# Part 3. Current Progress**



目前完成：



\`\`\`text

[OK] SOLA environment

[OK] PyTorch + CUDA

[OK] GroundingDINO

[OK] GroundingDINO CUDA extension

[OK] SAM2

[OK] GroundingDINO checkpoint

[OK] SAM2 checkpoints

[OK] MP4 → Frames

[OK] GroundingDINO single-frame inference

[OK] GroundingDINO batch inference

[OK] athlete + box_threshold=0.4 初步可以抓出選手



[OK] GroundingDINO bbox → SAM2 prompt mask

[OK] SAM2 video tracking（4 支測試影片初步正常）

[OK] 初步檢查 track 中斷 / ID switch（目前 4 支測試影片未發現明顯問題）

[ ] SOLA training

[ ] SOLA target-player inference

\`\`\`



**---**



**# Part 4. Next Step**



下一步：



\`\`\`text

GroundingDINO 偵測出的 Player bbox

                ↓

SAM2 初始化 Player ID

                ↓

SAM2 propagate 整段影片

                ↓

產生 Player Mask / Track

\`\`\`



主要檢查：



\`\`\`text

1\. 每個選手是否可以一路追蹤

2\. Track 是否會中斷

3\. 兩個選手是否會發生 ID switch

4\. Mask 是否會跳到裁判或背景

\`\`\`



如果 tracking 品質可接受，再開始訓練 SOLA。



目前沒有找到官方直接提供的 SOLA pretrained checkpoint，因此完整 SOLA inference 前，預計需要自己訓練 track-selection module。

---

# Part 5. SAM2 Track Test

## 18. `test_track.py` 放置位置

目前測試腳本放在：

```text
/home/code-server/cyt/SOLA/track_generation/test_track.py
```

目前的用途不是做最後的 SOLA target selection，而是先驗證：

```text
Frames
  ↓
GroundingDINO 找 athlete candidate
  ↓
SAM2 Image Predictor 把 bbox 轉成 prompt mask
  ↓
SAM2 Video Predictor 往前 / 往後追完整段影片
  ↓
產生 candidate tracks + SAM2 object tokens
  ↓
用 SOLA 類似的 IoU 規則過濾重複 prompt
```

目前 GroundingDINO 使用：

```text
prompt = athlete
box_threshold = 0.4
text_threshold = 0.25
```

這是目前桌球資料的測試設定，不代表所有資料都一定適合。

---

## 19. SAM2 Repo 路徑注意事項

目前 SAM2 repository 使用：

```text
/home/code-server/cyt/SOLA/track_generation/sam2_repo
```

不是：

```text
/home/code-server/cyt/SOLA/track_generation/sam2
```

原因是如果 repository 目錄本身叫 `sam2`，又直接從：

```text
/home/code-server/cyt/SOLA/track_generation
```

執行 Python，可能會和真正的 Python package：

```text
sam2_repo/sam2/
```

發生名稱衝突。

目前 `test_track.py` 會在最前面加入：

```python
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SAM2_REPO = os.path.join(CURRENT_DIR, "sam2_repo")

if SAM2_REPO not in sys.path:
    sys.path.insert(0, SAM2_REPO)
```

因此可以直接留在：

```text
/home/code-server/cyt/SOLA/track_generation
```

執行。

SAM2 import 仍然是：

```python
from sam2.build_sam import build_sam2_video_predictor
```

`build_sam2` / `build_sam2_video_predictor` 是 function 名稱，`sam2` 才是 Python package 名稱。

---

## 20. 執行 `test_track.py`

進入：

```bash
conda activate sola
cd /home/code-server/cyt/SOLA/track_generation
```

目前測試指令：

```bash
python test_track.py \
  --input_dir /home/code-server/cyt/sola_track_test/frames/505_311 \
  --output_dir /home/code-server/cyt/sola_track_test/tracks/505_311 \
  --grounding_dino_cfg GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py \
  --grounding_dino_ckpt GroundingDINO/weights/groundingdino_swint_ogc.pth \
  --sam2_cfg configs/sam2.1/sam2.1_hiera_l.yaml \
  --sam2_ckpt sam2_repo/checkpoints/sam2.1_hiera_large.pt \
  --prompt "athlete" \
  --box_threshold 0.4 \
  --text_threshold 0.25 \
  --bin_size 4 \
  --miou_thresh 0.7
```

其中：

```text
--bin_size 4
```

代表每隔 4 個 frame 產生一次新的 GroundingDINO / SAM2 prompt mask。

注意：這不代表 SAM2 只追每 4 個 frame。

SAM2 仍然會對完整 frame sequence 做 tracking。

例如共有 8 frames：

```text
GroundingDINO prompt frames:
frame 0
frame 4

SAM2 tracking:
frame 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7
```

如果 prompt 是從中間 frame 建立，SAM2 會：

```text
往後 propagate
+
往前 reverse propagate
```

補完整段 track。

---

## 21. Prompt Filtering / 重複 Track 處理

原本最初的 `test_track.py` 測試版會：

```text
每一個 prompt
  ↓
各自跑一次完整 SAM2 track
```

所以如果：

```text
8 frames
bin_size = 4
4 個選手
```

而 frame 0、frame 4 都抓到同樣 4 個人，就可能看到：

```text
Track 0 ~ Track 7
```

這不是影片被拆成兩段。

而是：

```text
同一個人
從不同 sampled frame 初始化
→ 各自形成一條完整 track
```

現在的 `test_track.py` 已改成更接近正式 SOLA 的方式：

```text
先取一個還沒處理的 prompt
  ↓
SAM2 追成完整 track
  ↓
拿這條 track 到其他 prompt 所在 frame 比較 mask IoU
  ↓
如果 IoU > miou_thresh
  ↓
視為同一個物件的重複 prompt
  ↓
直接 filtered，不再重新跑另一條完整 track
```

目前：

```text
miou_thresh = 0.7
```

因此理想情況下，如果 4 個選手在不同 sampled frame 都被重複偵測：

```text
8 prompt candidates
  ↓
4 tracked
4 filtered
  ↓
Final tracks = 4
```

這個 filtering 的目的不是修正 SAM2 的 ID switch。

它主要是避免：

```text
同一個人
因為在多個 sampled frame 都被偵測到
→ 重複產生多條幾乎一樣的完整 track
```

---

## 22. 為什麼要從多個 Frame 產生 Prompt

多個 sampled frame 的主要作用不是把 track 分段後再拼起來。

而是：

```text
不同時間點建立候選 prompt
  ↓
避免只依賴單一 frame
```

例如某個 frame 可能有：

```text
遮擋
姿勢不完整
GroundingDINO 漏抓
SAM2 prompt mask 品質較差
```

因此從不同時間點建立 candidate，可以增加至少得到一個可用初始化的機會。

但是：

```text
好的 prompt frame
≠
保證 SAM2 後面永遠不會追錯
```

SAM2 後續仍可能因為：

```text
人物交錯
快速移動
遮擋
人物外觀相似
```

發生 tracking error 或 ID switch。

所以 prompt filtering 解決的是「重複 candidate」問題，不是 tracking error correction。

---

## 23. 目前 `test_track.py` 輸出

輸出位置例如：

```text
/home/code-server/cyt/sola_track_test/tracks/505_311/
```

內容：

```text
tracks/505_311/
├── tracking.mp4
├── track_info.json
├── track_masks/
│   ├── track_000/
│   ├── track_001/
│   └── ...
└── sam2_object_tokens/
    ├── 00000.npy
    ├── 00001.npy
    └── ...
```

### `tracking.mp4`

最主要的人工檢查檔案。

確認：

```text
1. 每條 Track 是否保持在同一個人
2. 是否有 ID switch
3. 是否會跳到裁判 / 背景
4. 快速移動時是否跟丟
5. segmentation mask 是否穩定
```

### `track_masks/`

保存每條 candidate track 每個 frame 的 binary mask。

### `sam2_object_tokens/`

保存 SAM2 的 `obj_ptr` object tokens。

後續 SOLA 的 language-aligned track selection 會需要使用 track feature / object token。

### `track_info.json`

保存目前 tracking / filtering 的基本資訊，例如：

```text
prompt
box_threshold
text_threshold
bin_size
miou_thresh
num_prompt_candidates
num_tracked
num_filtered
num_not_used
tracks
prompt_status
```

`prompt_status` 可以看到某個 prompt：

```text
有沒有被追蹤
有沒有被其他 Track filtered
filtered_by 是哪條 Track
filtered_iou 是多少
```

---

## 24. 目前測試觀察

目前已用以下 4 支桌球影片做初步 tracking 測試：

```text
461_100
505_311
508_443
622_005
```

目前人工觀察：

```text
GroundingDINO 可以找到主要比賽選手
SAM2 可以從 prompt mask 追完整段影片
目前沒有看到明顯 track 中斷
目前沒有看到明顯 ID switch
不同 sampled frame 初始化後的結果看起來非常接近
```

因此目前這 4 支短影片上：

```text
多個 sampled frame 的 prompt
可能有不少是重複資訊
```

但目前樣本數還很少，不能直接推論所有桌球影片都不需要多 frame prompt。

後續可以比較：

```text
只用第一個 frame 初始化
vs.
bin_size = 4 的多 frame prompt
```

觀察：

```text
candidate recall
tracking / ID switch
最後 track 品質
執行時間
```

如果結果長期幾乎相同，再考慮針對短桌球影片簡化 prompt generation。

---

## 25. 與正式 SOLA 還有的差異

目前 `test_track.py` 是為桌球資料做的測試腳本，已經加入正式 SOLA 類似的 prompt filtering，但還不是完整官方資料生成流程。

目前主要差異：

```text
1. GroundingDINO 固定使用 "athlete"
   正式 SOLA 原本使用 dataset 的 referring expression

2. 目前同一 frame 的 candidates 仍以較簡單方式逐條處理
   官方 generate_tokens_gdino.py 支援同 frame batching

3. 目前輸出以方便人工檢查為主
   tracking.mp4 + PNG masks + npy object tokens

4. 官方還會輸出正式的 masklet / RLE / runtime 資訊

5. 官方程式使用 BF16 autocast
   目前 GPU 是 Tesla V100，不使用 BF16
```

其中第 1 點是目前刻意的研究設計：

```text
GroundingDINO
→ 只找 athlete candidate

SOLA track selection
→ 再使用完整動作文字判斷主要擊球者
```

這和原始 SOLA 把 referring expression 直接給 GroundingDINO 的方式不同，之後可以另外做比較。

---

# Part 6. Updated Progress

目前完成：

```text
[OK] SOLA environment
[OK] PyTorch + CUDA
[OK] GroundingDINO
[OK] GroundingDINO CUDA extension
[OK] SAM2
[OK] GroundingDINO checkpoint
[OK] SAM2 checkpoints
[OK] MP4 → Frames
[OK] GroundingDINO single-frame inference
[OK] GroundingDINO batch inference
[OK] athlete + box_threshold=0.4 初步可以抓出選手
[OK] GroundingDINO bbox → SAM2 prompt mask
[OK] SAM2 forward / backward video tracking
[OK] SOLA-style duplicate prompt filtering
[OK] 儲存 track masks / SAM2 object tokens
[OK] 4 支桌球影片初步 tracking 檢查

[ ] 擴大影片數量測試 tracking 穩定性
[ ] 比較 single-frame initialization vs. multi-frame prompt
[ ] 整理成正式 SOLA training 所需格式
[ ] SOLA training
[ ] SOLA target-player inference
```

