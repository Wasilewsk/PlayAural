game-name-holdem = Poker Texas Hold'em

holdem-set-starting-chips = Số chip ban đầu: { $count }
holdem-enter-starting-chips = Nhập số chip ban đầu
holdem-option-changed-starting-chips = Số chip ban đầu đã được đặt là { $count }.

holdem-set-big-blind = Mù lớn: { $count }
holdem-enter-big-blind = Nhập tiền mù lớn
holdem-option-changed-big-blind = Tiền mù lớn đã được đặt là { $count }.

holdem-set-ante = Cược góp: { $count }
holdem-enter-ante = Nhập tiền cược góp
holdem-option-changed-ante = Tiền cược góp đã được đặt là { $count }.

holdem-set-ante-start = Cược góp bắt đầu từ cấp: { $count }
holdem-enter-ante-start = Nhập cấp độ mù để bắt đầu có cược góp
holdem-option-changed-ante-start = Cấp độ bắt đầu cược góp đã được đặt là { $count }.

holdem-set-turn-timer = Thời gian mỗi lượt: { $mode }
holdem-select-turn-timer = Chọn thời gian mỗi lượt
holdem-option-changed-turn-timer = Thời gian mỗi lượt đã được đặt là { $mode }.

holdem-set-blind-timer = Thời gian tăng mù: { $mode }
holdem-select-blind-timer = Chọn thời gian tăng mù
holdem-option-changed-blind-timer = Thời gian tăng mù đã được đặt là { $mode }.

holdem-set-raise-mode = Chế độ tố: { $mode }
holdem-select-raise-mode = Chọn chế độ tố
holdem-option-changed-raise-mode = Chế độ tố đã được đặt là { $mode }.

holdem-set-max-raises = Số lần tố tối đa trong mỗi vòng cược: { $count }
holdem-enter-max-raises = Nhập số lần tố tối đa trong mỗi vòng cược (0 để không giới hạn)
holdem-option-changed-max-raises = Số lần tố tối đa trong mỗi vòng cược đã được đặt là { $count }.

holdem-error-big-blind-too-high = Mù lớn ({ $blind } chip) phải thấp hơn số chip ban đầu ({ $chips } chip).
holdem-error-ante-too-high = Cược góp ({ $ante } chip) phải thấp hơn số chip ban đầu ({ $chips } chip).
holdem-error-forced-bets-too-high = Khi cược góp có hiệu lực từ cấp 0, cược góp cộng mù lớn ({ $ante } + { $blind } chip) phải thấp hơn số chip ban đầu ({ $chips } chip).

holdem-antes-posted = Mọi người đã đóng cược góp. Hũ hiện có { $amount } chip.
holdem-you-post-small-blind = Bạn đóng Mù nhỏ ({ $sb } chip). { $bb_player } đóng Mù lớn ({ $bb } chip).
holdem-you-post-big-blind = { $sb_player } đóng Mù nhỏ ({ $sb } chip). Bạn đóng Mù lớn ({ $bb } chip).
holdem-players-post-blinds = { $sb_player } đóng Mù nhỏ ({ $sb } chip). { $bb_player } đóng Mù lớn ({ $bb } chip).

holdem-raise-invalid = Hãy nhập một số nguyên lớn hơn 0 cho mức tố thêm.
holdem-raise-cap-reached = Vòng cược này đã đạt giới hạn { $count } lần tố. Bạn có thể theo hoặc bỏ bài.
holdem-raise-over-stack = Bạn muốn tố thêm { $requested } chip, nhưng chỉ còn { $chips } chip. Hãy nhập mức tố nhỏ hơn hoặc chọn Tất tay.
holdem-raise-too-small = Bạn muốn tố thêm { $requested } chip. Mức tố tối thiểu là { $minimum } chip.
holdem-raise-over-limit = Bạn muốn tố thêm { $requested } chip. Với { $mode ->
    [pot_limit] chế độ giới hạn theo hũ
    [double_pot] chế độ giới hạn gấp đôi hũ
   *[other] chế độ tố đã chọn
}, sau khi theo, bạn chỉ có thể tố thêm tối đa { $maximum } chip.
holdem-all-in-over-limit = Bạn không thể tất tay với { $stack } chip còn lại vì { $mode ->
    [pot_limit] chế độ giới hạn theo hũ
    [double_pot] chế độ giới hạn gấp đôi hũ
   *[other] chế độ tố đã chọn
} hiện chỉ cho phép tố thêm tối đa { $maximum } chip sau khi theo. Hãy dùng Tố để nhập một mức hợp lệ.
holdem-all-in-raise-cap-reached = Bạn không thể tất tay dưới dạng một lần tố đủ mức vì vòng cược đã đạt giới hạn { $count } lần tố. Bạn có thể theo hoặc bỏ bài.
holdem-all-in-unavailable-raise-cap = Tất tay không dùng được vì hành động này sẽ trở thành một lần tố đủ mức sau khi vòng cược đã đạt giới hạn tố. Bạn có thể theo hoặc bỏ bài.
holdem-all-in-unavailable-limit = Tất tay không dùng được vì số chip của bạn vượt quá giới hạn cược hiện tại. Hãy dùng Tố để nhập một mức hợp lệ.
holdem-raise-unavailable-cap = Bạn không thể tố vì vòng cược này đã đạt giới hạn số lần tố.
holdem-raise-unavailable-limit = Bạn không thể tố đủ mức với số chip và giới hạn cược hiện tại. Bạn có thể theo, bỏ bài, hoặc tất tay khi hành động đó hợp lệ.

holdem-current-bet = Mức cược hiện tại trên bàn là { $amount } chip.
holdem-raise-range = Mức tố tối thiểu là { $minimum } chip. Sau khi theo, bạn có thể tố thêm tối đa { $maximum } chip.
holdem-no-full-raise-available = Bạn cần { $to_call } chip để theo và chỉ còn { $chips } chip, nên không thể tố đủ mức. Bạn có thể theo bằng cách tất tay hoặc bỏ bài.
holdem-button-unavailable = Ván hiện tại chưa có vị trí nút.
holdem-position-unavailable = Bạn không còn trong ván hiện tại nên không có vị trí cược.
holdem-reveal-no-live-hand = Bạn chỉ có thể đọc bài tẩy khi đã vào Ngửa bài với một tay bài còn hiệu lực.
holdem-private-hand-unavailable = Bạn đã hết chip và không còn tay bài hiệu lực để đọc.

holdem-winner-chips = { $rank }. { $player }: { $chips } chip
