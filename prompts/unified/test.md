# 桌球影片細粒度動作觀察

你會看到同一段桌球短影片依照時間順序排列的影像。

你的任務不是判斷動作類別，也不要猜測這個動作的名稱。

你的唯一任務是根據影片中實際可觀察到的內容，分析擊球動作的視覺與時間特徵。

所有判斷都必須來自影像本身。

如果某項資訊無法可靠判斷，請輸出 `"unclear"`，不要根據常見桌球動作自行推測。

---

## 1. 擊球事件

先確認影片中是否存在有效擊球。

判斷：

* 是否有球員完成擊球
* 哪一位球員是主要擊球者
* 擊球大約發生在影片的 early / middle / late
* 是否能直接觀察到球拍接近或接觸球
* 是否為發球動作
* 是否有明顯拋球

若無法確認擊球，不要根據後續姿勢推測一定有擊球。

---

## 2. 引拍

觀察擊球前的球拍與手臂移動。

判斷：

* `backswing_present`

  * yes
  * no
  * unclear

* `backswing_direction`

  * backward
  * backward-up
  * backward-down
  * lateral
  * minimal
  * unclear

* `backswing_amplitude`

  * none
  * small
  * medium
  * large
  * unclear

---

## 3. 擊球附近的球拍運動

只根據擊球前後連續影像判斷。

* `stroke_direction`

  * forward
  * forward-up
  * forward-down
  * downward
  * upward
  * lateral
  * unclear

* `stroke_amplitude`

  * small
  * medium
  * large
  * unclear

* `stroke_motion`

  * compact
  * full
  * explosive
  * controlled
  * unclear

* `racket_stability_near_contact`

  * stable
  * moderate_movement
  * large_movement
  * unclear

不得因為認為它是某種桌球動作，就反推球拍應該如何移動。

---

## 4. 收拍

觀察擊球後球拍與手臂的移動。

* `follow_through_direction`

  * forward
  * forward-up
  * forward-down
  * downward
  * upward
  * lateral
  * minimal
  * unclear

* `follow_through_amplitude`

  * none
  * small
  * medium
  * large
  * unclear

---

## 5. 手腕與前臂

判斷：

* `wrist_motion`

  * none
  * slight
  * obvious
  * unclear

* `forearm_rotation`

  * none
  * slight
  * obvious
  * unclear

* `lateral_or_hook_motion`

  * yes
  * no
  * unclear

若手腕或球拍尺寸太小而無法辨識，必須輸出 `unclear`。

---

## 6. 身體動作

判斷：

* `body_rotation`

  * none
  * slight
  * obvious
  * unclear

* `weight_transfer`

  * none
  * forward
  * backward
  * downward
  * upward
  * unclear

* `body_height_change`

  * none
  * slight_down
  * obvious_down
  * upward
  * unclear

* `knee_bend`

  * none
  * slight
  * obvious
  * unclear

---

## 7. 空間位置

判斷：

* `hand_side`

  * forehand
  * backhand
  * unclear

* `distance_from_table`

  * over_table
  * close
  * mid
  * far
  * unclear

* `contact_height`

  * low
  * normal
  * high
  * unclear

* `contact_area`

  * near_net
  * over_table
  * outside_table
  * unclear

---

## 8. 球與來球情境

只有球的位置與移動足夠清楚時才判斷。

* `ball_visible`

  * yes
  * partial
  * no

* `incoming_ball_context`

  * slow_or_controlled
  * normal
  * fast_or_attacking
  * unclear

* `outgoing_ball_trajectory`

  * low
  * normal
  * high_arc
  * unclear

不要推測無法直接觀察到的旋轉種類。

---

## 9. 動作主動程度

這一項不能只根據主觀印象判斷。

必須綜合：

* 引拍幅度
* 揮拍幅度
* 擊球附近球拍運動
* 身體轉動
* 重心變化
* 收拍幅度

判斷：

* `active_force_level`

  * low
  * medium
  * high
  * unclear

* `passive_redirection_level`

  * low
  * medium
  * high
  * unclear

並提供一段非常簡短的可觀察依據。

---

## 重要規則

1. 不要判斷這是哪一種桌球動作。
2. 不要輸出任何動作類別名稱。
3. 不要根據常識補充影片中看不到的資訊。
4. 每個欄位都必須回答。
5. 無法辨識時使用 `"unclear"`。
6. 不要因為前面某個判斷而強迫後面的觀察與它一致。
7. 只描述真正能從影片時間序列確認的內容。

---

## 輸出格式

只能輸出合法 JSON：

{
"hit_event": {
"valid_hit": "yes | no | unclear",
"main_actor": "<簡短描述>",
"contact_timing": "early | middle | late | unclear",
"contact_visible": "yes | no | unclear",
"is_serve": "yes | no | unclear",
"ball_toss_visible": "yes | no | unclear"
},
"backswing": {
"present": "yes | no | unclear",
"direction": "backward | backward-up | backward-down | lateral | minimal | unclear",
"amplitude": "none | small | medium | large | unclear"
},
"stroke": {
"direction": "forward | forward-up | forward-down | downward | upward | lateral | unclear",
"amplitude": "small | medium | large | unclear",
"motion": "compact | full | explosive | controlled | unclear",
"racket_stability_near_contact": "stable | moderate_movement | large_movement | unclear"
},
"follow_through": {
"direction": "forward | forward-up | forward-down | downward | upward | lateral | minimal | unclear",
"amplitude": "none | small | medium | large | unclear"
},
"wrist_forearm": {
"wrist_motion": "none | slight | obvious | unclear",
"forearm_rotation": "none | slight | obvious | unclear",
"lateral_or_hook_motion": "yes | no | unclear"
},
"body": {
"rotation": "none | slight | obvious | unclear",
"weight_transfer": "none | forward | backward | downward | upward | unclear",
"height_change": "none | slight_down | obvious_down | upward | unclear",
"knee_bend": "none | slight | obvious | unclear"
},
"spatial": {
"hand_side": "forehand | backhand | unclear",
"distance_from_table": "over_table | close | mid | far | unclear",
"contact_height": "low | normal | high | unclear",
"contact_area": "near_net | over_table | outside_table | unclear"
},
"ball_context": {
"ball_visible": "yes | partial | no",
"incoming_ball_context": "slow_or_controlled | normal | fast_or_attacking | unclear",
"outgoing_ball_trajectory": "low | normal | high_arc | unclear"
},
"action_dynamics": {
"active_force_level": "low | medium | high | unclear",
"passive_redirection_level": "low | medium | high | unclear",
"evidence": "<簡短列出實際可觀察依據>"
}
}
