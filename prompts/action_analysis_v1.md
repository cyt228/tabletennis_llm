你會看到一段 1 到 2 秒的桌球比賽影片。

請只根據影片中看得到的內容，分析這段影片中的動作情況。

請回答以下內容：

1. 這段影片比較像是 singles、doubles，或 uncertain
2. 畫面中的主要球員分別在做什麼動作
3. 誰是這段影片中的主要動作者
4. 用 2 到 4 句簡短總結這段動作

請注意：
- 如果不確定，請明確寫 uncertain
- 不要編造畫面中看不到的資訊
- 不要假設一定有成功擊球，除非畫面很明顯
- 若是雙打，盡量區分不同球員的角色或位置

請盡量用 JSON 格式輸出，格式如下：

{
  "match_type": "singles | doubles | uncertain",
  "main_actor": "簡短描述主要動作者，若不確定則寫 uncertain",
  "players_analysis": [
    {
      "player_ref": "left_side / right_side / left_front / left_back / right_front / right_back / uncertain",
      "action": "ready / swing / follow-through / movement / unclear",
      "summary": "簡短描述"
    }
  ],
}