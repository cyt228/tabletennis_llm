from schemas.records import PersonRecord, TableRecord


class PlayerFilter:
    def __init__(
        self,
        max_players_per_side: int = 2,
        umpire_zone_ratio_top: float = 0.35,
        outside_margin_x_ratio: float = 0.75,
    ):
        self.max_players_per_side = max_players_per_side
        self.umpire_zone_ratio_top = umpire_zone_ratio_top
        self.outside_margin_x_ratio = outside_margin_x_ratio

    def filter(
        self,
        persons: list[PersonRecord],
        table: TableRecord,
        frame_shape,
    ) -> list[PersonRecord]:

        h, w = frame_shape[:2]

        # 預設全部當 player
        for p in persons:
            p.role = "player"

        if not table.detected:
            return persons

        tx1, ty1, tx2, ty2 = table.bbox
        table_width = tx2 - tx1

        # 把 other 的範圍放很寬
        outside_margin_x = table_width * self.outside_margin_x_ratio
        play_x_min = tx1 - outside_margin_x
        play_x_max = tx2 + outside_margin_x

        active_candidates = []

        # Step 1: only very extreme outside-x becomes other
        for p in persons:
            fx, fy = p.foot_point

            far_outside_x = fx < play_x_min or fx > play_x_max

            if far_outside_x:
                p.role = "other"
            else:
                active_candidates.append(p)

        # Step 2: find umpire
        remain_candidates = []
        table_center_x = (tx1 + tx2) / 2

        for p in active_candidates:
            fx, fy = p.foot_point
            _, cy = p.center

            is_top_zone = cy < h * self.umpire_zone_ratio_top
            is_near_mid_x = (tx1 - 0.2 * table_width) <= fx <= (tx2 + 0.2 * table_width)

            if is_top_zone and is_near_mid_x:
                p.role = "umpire"
            else:
                remain_candidates.append(p)

        # 剩下全部保留 player
        return persons