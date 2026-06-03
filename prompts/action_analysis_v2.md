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

請只用以下 JSON 格式輸出：

{
  "predicted_label": 0
}
