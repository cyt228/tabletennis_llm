你會看到一段桌球影片，請判斷「正在擊球的球員」所執行的桌球動作類別。

你的任務：
只輸出最可能的 1 個類別代碼，格式必須是 JSON。

請根據影片 frames 與下方 action guide 進行判斷。

重要原則：
1. 影片 frames 是主要依據。
2. action guide 是分類標準，來自外部 CSV / Excel。
3. 若球員沒有明確擊球、發球、或完整桌球技術動作，選 0。
4. 若是發球動作，優先只在 15、16、17、18 中選。
5. 若不是發球，而是一般回合中的擊球，優先只在 1–14 中選。
6. 若類別相似，請依照 action guide 中的「主要判斷特徵」選擇最符合畫面證據的類別。
7. 不要輸出推理過程。
8. 不要輸出 markdown code block。
9. 即使不確定，也要選出最可能的一個類別。

Action guide:
{{ACTION_GUIDE}}

---

# 統一輸出格式（v2–v8 共用）

為了後續進行一致的結果分析，所有版本都必須輸出相同欄位。

請注意：
- 下列欄位只是統一紀錄格式，不代表你需要使用任何未在本版本前文中定義的額外判斷流程。
- `observed_evidence` 只能描述影片影格中實際可觀察到的內容，不要補充看不到的資訊。
- `decision_reason` 只需簡短說明最終分類依據，不要輸出完整思考過程。
- `closest_alternative` 請填入最接近但次佳的另一個類別代碼。
- `alternative_reason` 只需簡短說明為什麼目前分類比該替代類別更符合。
- `confidence` 是模型對本次判斷的自評信心值，只作為後續分析輔助，不代表真實機率。
- `coarse_category` 對應如下：
  - 0 → zero
  - 1–7 → attack
  - 8–11 → control
  - 12–14 → defensive
  - 15–18 → serve
- 只能輸出合法 JSON。
- 不要輸出 markdown code block。
- 不要輸出 JSON 以外的其他文字。

輸出格式：
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
