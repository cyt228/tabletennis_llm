# v2–v8 Prompt 統一版：版本差異、輸出欄位與文獻整理

## 1. 實驗範圍

v1 不納入目前的 19 類桌球動作分類比較。v1 的任務是一般影片理解與主要動作者描述，並非 0–18 細粒度動作分類。

正式 Prompt 演進比較從 v2 到 v8。

---

## 2. 統一輸出格式

為了後續可以同時分析分類結果、類別偏差與錯誤原因，v2–v8 全部改為相同 JSON schema：

```json
{
  "predicted_label": <0 到 18 的整數>,
  "coarse_category": "zero | attack | control | defensive | serve",
  "main_actor": "<簡短描述被判定為本次擊球者>",
  "observed_evidence": [
    "<可直接從影片影格確認的證據 1>",
    "<可直接從影片影格確認的證據 2>"
  ],
  "decision_reason": "<簡短說明上述證據為什麼支持 predicted_label>",
  "closest_alternative": <0 到 18 的整數>,
  "alternative_reason": "<簡短說明為什麼 predicted_label 比 closest_alternative 更符合>",
  "confidence": <0.0 到 1.0 的數值>
}
```

### 欄位用途

- `predicted_label`：19 類 Accuracy、Confusion Matrix。
- `coarse_category`：五大類 Accuracy、Recall，以及 Attack / Serve 等偏差分析。
- `main_actor`：分析模型是否找錯本次擊球者。
- `observed_evidence`：分析模型實際觀察到哪些視覺證據。
- `decision_reason`：區分「證據看對但分類錯」與「視覺觀察本身就錯」。
- `closest_alternative`：分析最常出現的細粒度混淆組合。
- `alternative_reason`：檢查模型是否理解相近類別的差異。
- `confidence`：分析高信心錯誤、低信心正確等現象；只能視為模型自評，不能當作真實機率。

### 很重要：統一輸出不等於統一推理方法

這次只統一「最後要留下哪些結果」，不把後面版本的推理邏輯加回前面版本。

例如：
- v2 可以輸出 evidence，但不會加入 v8 的 temporal evidence 規則。
- v3 可以輸出 closest alternative，但不會加入 v5 的 confusion rules。
- v6 可以輸出 main_actor，但不會加入 v8 的「先找真正擊球者」流程。
- v8 仍保留自己特有的 temporal sequence、hitter identification 與跨影格 evidence 要求。

這樣可以同時保留版本差異，又讓後續錯誤分析有一致資料。

---

## 3. v2–v8 版本差異

| 版本 | 核心設計 | 主要新增內容 | 想驗證的問題 |
|---|---|---|---|
| v2 | Label-only classification | 只有 0–18 類別名稱與分類任務 | 不提供動作知識時，Gemini 單靠視覺與 label 名稱的能力 |
| v3 | Action description | 加入每類簡要動作描述與觀察提示 | 類別語意與動作描述能否改善分類 |
| v4 | Hierarchical reasoning | 有效擊球 → 發球/非發球 → 大類 → 細分類 | 分層、coarse-to-fine 判斷是否有效 |
| v5 | Structured prompt + confusion rules | 重整結構，加入易混淆類別的明確對照 | 更清楚的規則與 pairwise discrimination 是否改善辨識 |
| v6 | External action guide | 將完整分類知識改由外部 ACTION_GUIDE 提供 | 更完整、可維護的外部 action knowledge 是否有效 |
| v7 | Action guide + hierarchical reasoning | ACTION_GUIDE + 大類與分層流程 | 完整知識與 structured reasoning 是否互補 |
| v8 | Temporal evidence reasoning | 把多幀視為時間序列、先找真正擊球者、要求跨影格證據 | temporal dynamics 與 evidence-based classification 是否改善細粒度辨識 |

---

## 4. 各版本研究角色

### v2 — Label-only baseline
- 只提供 0–18 類別名稱。
- 不提供動作判斷特徵。
- 不提供分層流程。
- 不提供混淆規則。
- 不使用外部 action guide。

用途：最乾淨的 Prompt baseline。

### v3 — Action description
相較 v2：
- 加入站位、揮拍方向、球高與動作目的等觀察提示。
- 每個類別加入簡要動作描述。

用途：測試 textual action knowledge 是否有幫助。

### v4 — Hierarchical reasoning
相較 v3：
- 加入明確分步流程。
- 先判斷是否有擊球，再判斷是否發球。
- 非發球再分 Attack / Control / Defensive，最後才細分類。
- 加入較完整優先規則。

用途：測試 coarse-to-fine / structured reasoning。

### v5 — Structured prompt / explicit confusion rules
與 v4 的核心分類知識接近，但：
- Prompt 結構更清楚。
- 類別段落重新整理。
- 用「1 vs 2 vs 5 vs 13」、「4 vs 7 vs 11」等方式直接比較易混淆類別。

用途：比較 prompt organization 與 explicit pairwise discrimination。

注意：v4 → v5 不是完全單一變因，而是一次 prompt refinement。

### v6 — External action guide
- 類別知識改由 `{{ACTION_GUIDE}}` 動態注入。
- Prompt 本身只保留少量原則。

用途：測試外部、可更新的完整 action knowledge。

注意：有外部 guide 不代表已經是 RAG；沒有 retrieval 流程時，不應直接稱為 RAG。

### v7 — External action guide + hierarchy
相較 v6：
- 保留 ACTION_GUIDE。
- 再加入 Step 1–4 structured reasoning。
- 明確區分 Attack / Control / Defensive / Serve。

用途：測試「完整知識 + 分層推理」是否優於只提供知識。

### v8 — Temporal evidence version
主要新增：
- 明確告知輸入圖片依時間排序。
- 要求將多幀視為同一段連續動作。
- 先判斷真正正在擊球的球員。
- 利用球員、球拍、手臂、身體位置的跨影格變化。
- 要求 evidence 支持分類。
- 強調不要依單張畫面或無法觀察的資訊猜測。

用途：測試 temporal understanding / motion evidence 是否能改善前面仍存在的細粒度問題。

重要限制：
- 原始 v8 不是嚴格的「v7 + temporal only」。
- v7 使用外部 ACTION_GUIDE，但原始 v8 又把完整類別描述直接寫回 Prompt。
- 若日後要做嚴格 ablation，建議另外製作 `v7 + temporal only` 控制版本。

---

## 5. 建議的結果分析

### 第一層：分類結果
- 19-class Accuracy
- 5-class Accuracy
- Per-class Recall
- Confusion Matrix
- Prediction distribution

### 第二層：錯誤型態
- Actor error：找錯本次擊球者
- Observation error：可見動作特徵看錯
- Reasoning / classification error：證據合理但最後映射到錯誤 label
- Fine-grained confusion：與 closest alternative 混淆
- Prompt bias：例如 Serve 或 Attack 被某個流程過度放大

### 第三層：evidence 分析
- evidence 是否真的能從影格驗證
- evidence 是否包含關鍵 motion cue
- 高信心錯誤是否集中在特定類別
- 相同 GT 在不同 prompt 下，evidence 是否改變

---

## 6. 文獻對應

以下是「設計概念參考」，不是宣稱文獻採用了完全相同的 Prompt。

### v2：VLM / zero-shot action recognition baseline
可參考：
- Radford et al., 2021, CLIP: Learning Transferable Visual Models From Natural Language Supervision.
- Ni et al., 2022, ActionCLIP: A New Paradigm for Video Action Recognition.

可支持：
- 使用文字標籤與視覺表徵進行 zero-shot / transfer recognition 的概念。

### v3：Action description / textual semantics
可參考：
- ActionCLIP (Ni et al., 2022)
- X-CLIP (Ni et al., 2022)

可支持：
- 動作類別文字語意與影片表徵結合的方向。
- 不能直接說「手寫描述一定會提高 Gemini 準確率」。

### v4 / v7：Step-by-step / hierarchical reasoning
可參考：
- Wei et al., 2022, Chain-of-Thought Prompting Elicits Reasoning in Large Language Models.
- Kojima et al., 2022, Large Language Models are Zero-Shot Reasoners.

可支持：
- 把複雜判斷拆成中間步驟的概念。
- 本研究把它轉成「是否發球 → 大類 → 細分類」。

### v5：Confusion-aware / discriminative prompting
可對應概念：
- contrastive reasoning
- class discrimination
- pairwise comparison

適合論文表述：
- v5 是 discriminative prompt design / explicit confusion rules。
- 不宜宣稱存在一篇論文與 v5 設計完全相同。

### v6 / v7：External knowledge
可參考：
- Lewis et al., 2020, Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.

可支持：
- 外部知識輔助模型判斷的概念。

注意：
- v6 / v7 目前是 external guide injection，不是完整 RAG。
- 等真正加入 retrieval 時，再補 multimodal RAG / knowledge-augmented VLM 文獻會更合理。

### v8：Temporal / fine-grained motion understanding
可參考：
- MVBench: A Comprehensive Multi-modal Video Understanding Benchmark.
- MotionBench: Benchmarking and Improving Fine-grained Video Motion Understanding.
- FineBench：細粒度影片 / 動作理解相關 benchmark；正式論文名稱與版本請以實際引用來源為準。

可支持：
- VLM 在 temporal reasoning、motion understanding、fine-grained action discrimination 仍存在明顯困難。
- 與 v8 強調跨影格 motion evidence 的研究動機最直接。

---

## 7. 建議論文中的 Prompt Ablation 表

| Prompt | Label only | Action description | Hierarchy | Confusion rules | External guide | Temporal evidence | 19-class Acc. | 5-class Acc. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v2 | ✓ |  |  |  |  |  |  |  |
| v3 | ✓ | ✓ |  |  |  |  |  |  |
| v4 | ✓ | ✓ | ✓ | 部分 |  |  |  |  |
| v5 | ✓ | ✓ | ✓ | ✓ |  |  |  |  |
| v6 | ✓ | via guide |  |  | ✓ |  |  |  |
| v7 | ✓ | via guide | ✓ |  | ✓ |  |  |  |
| v8 | ✓ | ✓ | ✓ | ✓ |  | ✓ |  |  |

這張表可以回答：
「在不修改模型參數，只逐步改 Prompt 與提供資訊的情況下，效果可以改善到什麼程度？」

若 v2 → v8 提升仍有限，就能合理引出下一階段：
- knowledge retrieval
- few-shot example retrieval
- keypoint / pose
- agent-based evidence selection
- 或其他非單純 Prompt engineering 的方法
