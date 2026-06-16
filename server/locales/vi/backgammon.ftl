# Backgammon localization

game-name-backgammon = Cờ thỏ cáo

# Colors
backgammon-color-red = đỏ
backgammon-color-white = trắng

# Menu helpers
backgammon-unavailable = không khả dụng

# Game start
backgammon-game-started = { $red } chơi Đỏ, { $white } chơi Trắng.
backgammon-opening-roll = Lượt tung mở màn: { $red } tung được { $red_die }, { $white } tung được { $white_die }.
backgammon-opening-tie = Cả hai đều tung được { $die }, tung lại.
backgammon-opening-winner-you = Bạn đi trước với { $die1 } và { $die2 }.
backgammon-opening-winner-player = { $player } đi trước với { $die1 } và { $die2 }.

# Dice
backgammon-roll-you = Bạn tung được { $die1 } và { $die2 }.
backgammon-roll-player = { $player } tung được { $die1 } và { $die2 }.

# No moves
backgammon-no-moves-you = Bạn không còn nước đi hợp lệ, nên lượt của bạn kết thúc.
backgammon-no-moves-player = { $player } không còn nước đi hợp lệ, nên lượt của họ kết thúc.

# Brief move commentary
backgammon-brief-move-normal = { $is_self ->
    [yes] Bạn đi một quân.
    *[no] { $player } đi một quân.
}
backgammon-brief-move-hit = { $is_self ->
    [yes] Bạn bắt quân của { $opponent }.
    [spectator] { $player } bắt quân của { $opponent }.
    *[no] { $player } bắt quân của bạn.
}
backgammon-brief-move-bar = { $is_self ->
    [yes] Bạn nhập quân từ thanh.
    *[no] { $player } nhập quân từ thanh.
}
backgammon-brief-move-bar-hit = { $is_self ->
    [yes] Bạn nhập quân từ thanh và bắt quân của { $opponent }.
    [spectator] { $player } nhập quân từ thanh và bắt quân của { $opponent }.
    *[no] { $player } nhập quân từ thanh và bắt quân của bạn.
}
backgammon-brief-move-bearoff = { $is_self ->
    [yes] Bạn đưa một quân ra khỏi bàn.
    *[no] { $player } đưa một quân ra khỏi bàn.
}

# Verbose move commentary
backgammon-verbose-move-normal = { $is_self ->
    [yes] Bạn di chuyển một quân từ điểm { $src } đến điểm { $dest }.
    *[no] { $player } di chuyển một quân từ điểm { $src } đến điểm { $dest }.
} { $src_count ->
    [0] Điểm { $src } hiện đã trống, { $dest_count } ở điểm { $dest }.
    *[other] { $src_count } hiện ở điểm { $src }, { $dest_count } ở điểm { $dest }.
}
backgammon-verbose-move-hit = { $is_self ->
    [yes] Bạn di chuyển một quân từ điểm { $src } để bắt quân của { $opponent } ở điểm { $dest }.
    [spectator] { $player } di chuyển một quân từ điểm { $src } để bắt quân của { $opponent } ở điểm { $dest }.
    *[no] { $player } di chuyển một quân từ điểm { $src } để bắt quân của bạn ở điểm { $dest }.
} { $src_count ->
    [0] Điểm { $src } hiện đã trống.
    *[other] Còn { $src_count } ở điểm { $src }.
}
backgammon-verbose-move-bar = { $is_self ->
    [yes] Bạn nhập quân từ thanh vào điểm { $dest }.
    *[no] { $player } nhập quân từ thanh vào điểm { $dest }.
} hiện có { $dest_count } ở điểm { $dest }.
backgammon-verbose-move-bar-hit = { $is_self ->
    [yes] Bạn nhập quân từ thanh để bắt quân của { $opponent } ở điểm { $dest }.
    [spectator] { $player } nhập quân từ thanh để bắt quân của { $opponent } ở điểm { $dest }.
    *[no] { $player } nhập quân từ thanh để bắt quân của bạn ở điểm { $dest }.
}
backgammon-verbose-move-bearoff = { $is_self ->
    [yes] Bạn đưa quân ra từ điểm { $src }.
    *[no] { $player } đưa quân ra từ điểm { $src }.
} { $src_count ->
    [0] Điểm { $src } hiện đã trống.
    *[other] Còn { $src_count } ở điểm { $src }.
}

# Doubling
backgammon-doubles-you = Bạn đề nghị nhân đôi khối lên { $value }.
backgammon-doubles-player = { $player } đề nghị nhân đôi khối lên { $value }.
backgammon-accepts-you = Bạn chấp nhận nhân đôi và nhận quyền giữ khối.
backgammon-accepts-player = { $player } chấp nhận nhân đôi và nhận quyền giữ khối.
backgammon-drops-you = Bạn bỏ lời nhân đôi và chịu thua ván này theo giá trị khối hiện tại.
backgammon-drops-player = { $player } bỏ lời nhân đôi và chịu thua ván này theo giá trị khối hiện tại.
backgammon-accept = Chấp nhận
backgammon-drop = Bỏ

# Point labels
backgammon-point-empty = { $point }
backgammon-point-empty-selected = { $point } đã chọn
backgammon-point-occupied = { $point } { $color }, { $count }
backgammon-point-occupied-selected = { $point } { $color }, { $count } đã chọn

# Action labels
backgammon-label-double = Nhân đôi
backgammon-label-undo = Hoàn tác
backgammon-label-next = Tiếp
backgammon-label-previous = Trước
backgammon-label-deselect = Bỏ chọn
backgammon-label-next-destination = Điểm đến tiếp theo
backgammon-label-previous-destination = Điểm đến trước đó

# Selection feedback
backgammon-selected-point = Đã chọn điểm { $point }, { $count } quân.
backgammon-selected-bar = Đã chọn thanh.
backgammon-deselected = Đã bỏ chọn.
backgammon-no-checkers-there = Không có quân ở đó.
backgammon-not-your-checkers = Đó không phải quân của bạn.
backgammon-no-moves-from-here = Không có nước đi hợp lệ từ đây.
backgammon-must-enter-from-bar = Phải nhập quân từ thanh trước.
backgammon-illegal-move = Nước đi không hợp lệ.
backgammon-no-dice-remaining = Bạn không còn viên xúc xắc nào để dùng trong lượt này.
backgammon-no-checkers-on-bar = Bạn không có quân nào trên thanh để nhập vào bàn.
backgammon-invalid-destination = Đó không phải một điểm hợp lệ trên bàn cờ thỏ cáo.
backgammon-source-empty = Điểm { $point } không có quân để đi.
backgammon-source-opponent = Điểm { $point } đang có quân của đối thủ.
backgammon-destination-blocked = Điểm { $point } bị chặn bởi { $count } quân đối thủ.
backgammon-bar-entry-blocked = Bạn không thể nhập quân vào điểm { $point }; điểm đó bị chặn bởi { $count } quân đối thủ.
backgammon-no-die-for-bar-entry = Không viên xúc xắc nào còn lại ({ $dice }) nhập được quân vào điểm { $point }.
backgammon-no-die-for-destination = Không viên xúc xắc nào còn lại ({ $dice }) đi được từ điểm { $src } đến điểm { $dest }.
backgammon-must-use-forced-die = Lúc này bạn phải dùng { $dice }, vì cờ thỏ cáo bắt buộc dùng cả hai viên nếu có thể, hoặc dùng viên lớn hơn khi chỉ đi được một viên.
backgammon-bearoff-not-home = Bạn chưa thể đưa quân ra khỏi bàn vì chưa đưa toàn bộ quân vào khu nhà.
backgammon-bearoff-blocked = Bạn không thể đưa quân ra từ điểm { $point } với { $die }, vì còn quân ở điểm { $blocking_point } của bạn.
backgammon-bearoff-no-die = Bạn không thể đưa quân ra từ điểm { $point } với các xúc xắc còn lại ({ $die }).
backgammon-nothing-to-undo = Không có gì để hoàn tác.
backgammon-undone = Đã hoàn tác nước đi.
backgammon-cannot-double = Bạn không thể nhân đôi lúc này.
backgammon-cannot-undo = Không có gì để hoàn tác.
backgammon-not-doubling-phase = Không có lời nhân đôi nào để phản hồi.
backgammon-need-roll-first = Bạn cần tung xúc xắc trước khi di chuyển quân.
backgammon-confirm-drop-double = Bỏ lời nhân đôi sẽ chịu thua ván này theo giá trị khối hiện tại. Nhấn Bỏ lần nữa trong vòng 10 giây để xác nhận.

# Info keybinds
backgammon-check-status = Trạng thái
backgammon-check-cube = Khối nhân đôi
backgammon-check-pip = Số điểm pip
backgammon-check-score = Điểm
backgammon-check-score-detailed = Điểm chi tiết
backgammon-check-dice = Xúc xắc
backgammon-status = Thanh Đỏ: { $bar_red }. Thanh Trắng: { $bar_white }. Đỏ đã ra: { $off_red }. Trắng đã ra: { $off_white }.
backgammon-dice = { $dice }
backgammon-dice-none = Không còn xúc xắc.
backgammon-cube-status = Khối nhân đôi đang ở mức { $value }. { $owner ->
    [center] Ở giữa, cả hai người chơi đều có thể nhân đôi.
    *[other] Sở hữu bởi { $owner }.
} { $can_double ->
    [yes] Có thể nhân đôi ngay bây giờ.
    [crawford] Đây là ván Crawford, không được nhân đôi.
    *[no] Hiện không thể nhân đôi.
}
backgammon-cube-no-match = Không có khối nhân trong ván đơn.
backgammon-pip-count = Số điểm pip Đỏ: { $red_pip }. Số điểm pip Trắng: { $white_pip }.
backgammon-match-score-line = { $player }: { $score } trên { $match_length } điểm.
backgammon-match-score-cube-line = Khối nhân đôi: { $cube }.

# Scoring
backgammon-wins-game-you = Bạn thắng { $points } điểm.
backgammon-wins-game-player = { $player } thắng { $points } điểm.
backgammon-new-game = Bắt đầu ván { $number }.
backgammon-match-winner-you = Bạn thắng cả trận!
backgammon-match-winner-player = { $player } thắng cả trận!
backgammon-end-score = { $red } { $red_score } - { $white } { $white_score }. Trận đến { $match_length }.
backgammon-crawford = Ván Crawford: không nhân đôi ở ván này.

# Difficulty levels
backgammon-difficulty-random = Ngẫu nhiên
backgammon-difficulty-simple = Đơn giản

# Options
backgammon-option-match-length = Độ dài trận: { $match_length }
backgammon-option-select-match-length = Đặt độ dài trận (1-25)
backgammon-option-changed-match-length = Độ dài trận đã được đặt thành { $match_length }.
backgammon-option-bot-difficulty = Độ khó bot: { $bot_difficulty }
backgammon-option-select-bot-difficulty = Chọn độ khó bot
backgammon-option-changed-bot-difficulty = Độ khó bot đã được đặt thành { $bot_difficulty }.
