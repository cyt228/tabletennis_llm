你會看到一段桌球擊球影片。

你的任務是判斷「正在擊球的球員」所執行的球種。
請只從以下類別中選擇 1 個最可能的代碼輸出。

類別代碼：
0 = 無 none
1 = 拉球 drive
2 = 反拉 counter drive
3 = 殺球 smash
4 = 擰球 backhand twist
5 = 快帶 fast drive
6 = 推擠 fast push
7 = 挑撥 flip
8 = 拱球 pimple’s long push
9 = 磕球 pimple’s fast push
10 = 搓球 long push
11 = 擺短 drop shot
12 = 削球 chop
13 = 擋球 block
14 = 放高球 lob
15 = 傳統 traditional
16 = 勾手 hook
17 = 逆旋轉 reverse
18 = 下蹲式 squat

請注意：
- 只能輸出 1 個類別代碼
- 即使不確定，也要選出最可能的一個
- 不要輸出原因
- 不要輸出其他文字
- 不要輸出 markdown code block

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
