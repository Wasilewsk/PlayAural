game-name-farkle = Farkle

farkle-roll = Gieo { $count } { $count ->
    [one] viên
   *[other] viên
}
farkle-bank = Chốt { $points } điểm

farkle-take-single-one = Một con 1 được { $points } điểm
farkle-take-single-five = Một con 5 được { $points } điểm
farkle-take-three-kind = Ba con { $number } được { $points } điểm
farkle-take-four-kind = Bốn con { $number } được { $points } điểm
farkle-take-five-kind = Năm con { $number } được { $points } điểm
farkle-take-six-kind = Sáu con { $number } được { $points } điểm
farkle-take-small-straight = Sảnh nhỏ được { $points } điểm
farkle-take-large-straight = Sảnh lớn được { $points } điểm
farkle-take-three-pairs = Ba đôi được { $points } điểm
farkle-take-double-triplets = Hai bộ ba được { $points } điểm
farkle-take-full-house = Bốn con giống nhau kèm một đôi được { $points } điểm

farkle-you-roll = Bạn gieo { $count } { $count ->
    [one] viên
   *[other] viên
}.
farkle-player-rolls = { $player } gieo { $count } { $count ->
    [one] viên
   *[other] viên
}.
farkle-you-roll-brief = Bạn gieo { $count }.
farkle-player-rolls-brief = { $player } gieo { $count }.
farkle-roll-result = Xúc xắc ra: { $dice }.
farkle-roll-result-brief = Xúc xắc: { $dice }.

farkle-you-farkle = FARKLE! Bạn mất { $points } điểm trong lượt này.
farkle-player-farkles = FARKLE! { $player } mất { $points } điểm trong lượt này.
farkle-you-farkle-brief = Farkle: bạn mất { $points }.
farkle-player-farkles-brief = Farkle: { $player } mất { $points }.

farkle-you-take-combo = Bạn giữ { $combo } để lấy { $points } điểm.
farkle-player-takes-combo = { $player } giữ { $combo } để lấy { $points } điểm.
farkle-you-take-combo-brief = Bạn: { $combo }, +{ $points }.
farkle-player-takes-combo-brief = { $player }: { $combo }, +{ $points }.

farkle-you-hot-dice = Nóng tay! Bạn đã ghi điểm bằng cả sáu viên và có thể gieo lại đủ sáu viên.
farkle-player-hot-dice = Nóng tay! { $player } đã ghi điểm bằng cả sáu viên và có thể gieo lại đủ sáu viên.
farkle-you-hot-dice-brief = Bạn: nóng tay.
farkle-player-hot-dice-brief = { $player }: nóng tay.

farkle-you-bank = Bạn chốt { $points } điểm. Tổng điểm của bạn hiện là { $total }.
farkle-player-banks = { $player } chốt { $points } điểm, tổng cộng { $total }.
farkle-you-bank-brief = Bạn chốt { $points}; tổng { $total }.
farkle-player-banks-brief = { $player } chốt { $points}; tổng { $total }.

farkle-you-win = Bạn thắng với { $score } điểm!
farkle-winner = { $player } thắng với { $score } điểm!
farkle-you-win-brief = Bạn thắng: { $score }.
farkle-winner-brief = { $player } thắng: { $score }.
farkle-winners-tie = Hòa ở mốc mục tiêu! Những người vào loạt phân thắng bại: { $players }.
farkle-tiebreaker-round-start = Vòng phân thắng bại { $round }. Còn tranh tài: { $players }.

farkle-your-turn-score = Bạn đang có { $points } điểm trong lượt này.
farkle-turn-score = { $player } đang có { $points } điểm trong lượt này.
farkle-no-turn = Hiện không có ai đang chơi lượt.

farkle-set-target-score = Điểm mục tiêu: { $score }
farkle-enter-target-score = Nhập điểm mục tiêu (500-5000):
farkle-option-changed-target = Điểm mục tiêu đã đặt là { $score }.

farkle-set-entrance-score = Điểm nhập cuộc tối thiểu: { $score }
farkle-enter-entrance-score = Nhập điểm nhập cuộc tối thiểu (0-5000):
farkle-option-changed-entrance = Điểm nhập cuộc tối thiểu đã đặt là { $score }.

farkle-set-bank-score = Điểm chốt tối thiểu: { $score }
farkle-enter-bank-score = Nhập điểm chốt tối thiểu (0-5000):
farkle-option-changed-bank = Điểm chốt tối thiểu đã đặt là { $score }.

farkle-error-entrance-above-target = Điểm nhập cuộc tối thiểu ({ $entrance }) không được cao hơn điểm mục tiêu ({ $target }).
farkle-error-bank-above-target = Điểm chốt tối thiểu ({ $bank }) không được cao hơn điểm mục tiêu ({ $target }).

farkle-must-take-combo = Bạn phải giữ ít nhất một viên hoặc một tổ hợp có điểm trước khi gieo tiếp.
farkle-cannot-bank = Bạn chỉ có thể chốt sau khi đã giữ một viên hoặc một tổ hợp có điểm trong lượt này.
farkle-must-reach-entrance-score = Bạn cần ít nhất { $points } điểm trong lượt để chốt điểm lần đầu.
farkle-must-reach-bank-score = Bạn cần ít nhất { $points } điểm trong lượt để chốt.
farkle-confirm-risky-roll = Bạn có thể chốt { $points } điểm ngay bây giờ. Gieo tiếp có thể làm mất hết điểm lượt này; lặp lại Gieo trong { $seconds } giây để xác nhận.
farkle-invalid-combo-action = Lựa chọn ghi điểm này không hợp lệ. Hãy chọn một tổ hợp đang được hiển thị.
farkle-combo-no-longer-available = Tổ hợp ghi điểm đó không còn khả dụng. Danh sách lựa chọn hiện tại đã được làm mới.

farkle-combo-single-1 = Một con 1
farkle-combo-single-5 = Một con 5
farkle-combo-three-kind = Ba con { $number }
farkle-combo-four-kind = Bốn con { $number }
farkle-combo-five-kind = Năm con { $number }
farkle-combo-six-kind = Sáu con { $number }
farkle-combo-small-straight = Sảnh nhỏ
farkle-combo-large-straight = Sảnh lớn
farkle-combo-three-pairs = Ba đôi
farkle-combo-double-triplets = Hai bộ ba
farkle-combo-full-house = Bốn con giống nhau kèm một đôi

farkle-line-format = { $rank }. { $player }: { $points }
farkle-combo-fallback = { $combo } ({ $points } điểm)

farkle-check-turn-score = Xem điểm lượt này
farkle-roll-label = Gieo xúc xắc
farkle-bank-label = Chốt điểm
