game-name-fivecarddraw = Poker Rút năm lá

draw-set-starting-chips = Số chip ban đầu: { $count }
draw-enter-starting-chips = Nhập số chip ban đầu
draw-option-changed-starting-chips = Số chip ban đầu đã được đặt là { $count }.

draw-set-ante = Cược góp: { $count }
draw-enter-ante = Nhập mức cược góp
draw-option-changed-ante = Cược góp đã được đặt là { $count }.

draw-set-turn-timer = Thời gian mỗi lượt: { $mode }
draw-select-turn-timer = Chọn thời gian mỗi lượt
draw-option-changed-turn-timer = Thời gian mỗi lượt đã được đặt là { $mode }.

draw-set-raise-mode = Chế độ tố: { $mode }
draw-select-raise-mode = Chọn chế độ tố
draw-option-changed-raise-mode = Chế độ tố đã được đặt là { $mode }.

draw-set-max-raises = Số lần tố tối đa trong mỗi vòng cược: { $count }
draw-enter-max-raises = Nhập số lần tố tối đa trong mỗi vòng cược (0 để không giới hạn)
draw-option-changed-max-raises = Số lần tố tối đa trong mỗi vòng cược đã được đặt là { $count }.

draw-set-draw-limit = Luật đổi bài: { $mode }
draw-select-draw-limit = Chọn luật đổi bài
draw-option-changed-draw-limit = Luật đổi bài đã được đặt là { $mode }.
draw-limit-three-cards = Tối đa 3 lá (luật chuẩn)
draw-limit-four-with-ace = Tối đa 4 lá khi giữ lại một lá Át

draw-error-ante-too-high = Cược góp ({ $ante } chip) phải thấp hơn số chip ban đầu ({ $chips } chip) để người chơi vẫn còn chip ra quyết định sau khi chia bài.
draw-error-capped-mode-needs-ante = { $mode ->
    [pot_limit] Giới hạn theo hũ
    [double_pot] Giới hạn gấp đôi hũ
   *[other] Chế độ tố có giới hạn này
} yêu cầu cược góp lớn hơn 0 để người hành động đầu tiên có một mức cược dựa trên hũ.

draw-antes-posted = Mọi người đã đóng cược góp. Hũ hiện có { $amount } chip.
draw-betting-round-1 = Vòng cược đầu tiên.
draw-betting-round-2 = Vòng cược thứ hai.
draw-begin-draw = Giai đoạn đổi bài. Bắt đầu từ người còn trong ván đầu tiên bên trái người chia bài, hãy chọn bài để đổi hoặc giữ nguyên bài.
draw-not-draw-phase = Bạn chỉ có thể đổi bài sau vòng cược đầu tiên. Hãy tiếp tục bằng hành động cược hiện tại.
draw-not-betting = Bạn không thể cược trong giai đoạn đổi bài. Hãy chọn các lá muốn đổi, rồi chọn Đổi bài.
draw-fold-not-available = Bạn không thể bỏ bài trong giai đoạn đổi bài. Hãy chọn các lá muốn đổi, rồi chọn Đổi bài.

draw-toggle-discard = Chọn đổi lá bài thứ { $index }
draw-card-keep = { $card }
draw-card-discard = { $card }, đã chọn để đổi
draw-draw-cards = Đổi bài
draw-draw-cards-count = { $count ->
    [0] Giữ nguyên bài
    [one] Đổi 1 lá bài
   *[other] Đổi { $count } lá bài
}
draw-dealt-cards = Năm lá bài của bạn là { $cards }.
draw-you-drew-cards = { $count } { $count ->
    [one] lá bài thay thế của bạn là
   *[other] lá bài thay thế của bạn là
} { $cards }.
draw-you-draw = Bạn đổi { $count } { $count ->
    [one] lá bài
   *[other] lá bài
}.
draw-player-draws = { $player } đổi { $count } { $count ->
    [one] lá bài
   *[other] lá bài
}.
draw-you-stand-pat = Bạn giữ nguyên cả năm lá bài.
draw-player-stands-pat = { $player } giữ nguyên cả năm lá bài.
draw-you-discard-limit = Theo luật đổi bài đã chọn, bạn chỉ được đổi tối đa { $count } lá bài.
draw-four-requires-kept-ace = Muốn đổi 4 lá, bạn phải giữ lại ít nhất một lá Át. Hãy bỏ chọn một lá Át hoặc chỉ đổi tối đa 3 lá.

draw-raise-invalid = Hãy nhập một số nguyên lớn hơn 0 cho mức tố thêm.
draw-raise-cap-reached = Vòng cược này đã đạt giới hạn { $count } lần tố. Bạn có thể theo hoặc bỏ bài.
draw-raise-over-stack = Bạn muốn tố thêm { $requested } chip, nhưng chỉ còn { $chips } chip. Hãy nhập mức tố nhỏ hơn hoặc chọn Tất tay.
draw-raise-too-small = Bạn muốn tố thêm { $requested } chip. Mức tố tối thiểu là { $minimum } chip.
draw-raise-over-limit = Bạn muốn tố thêm { $requested } chip. Với { $mode ->
    [pot_limit] chế độ giới hạn theo hũ
    [double_pot] chế độ giới hạn gấp đôi hũ
   *[other] chế độ tố đã chọn
}, sau khi theo, bạn chỉ có thể tố thêm tối đa { $maximum } chip.
draw-all-in-over-limit = Bạn không thể tất tay với { $stack } chip còn lại vì { $mode ->
    [pot_limit] chế độ giới hạn theo hũ
    [double_pot] chế độ giới hạn gấp đôi hũ
   *[other] chế độ tố đã chọn
} hiện chỉ cho phép tố thêm tối đa { $maximum } chip sau khi theo. Hãy dùng Tố để nhập một mức hợp lệ.
draw-all-in-raise-cap-reached = Bạn không thể tất tay dưới dạng một lần tố đủ mức vì vòng cược đã đạt giới hạn { $count } lần tố. Bạn có thể theo hoặc bỏ bài.
draw-all-in-unavailable-raise-cap = Tất tay không dùng được vì hành động này sẽ trở thành một lần tố đủ mức sau khi vòng cược đã đạt giới hạn tố. Bạn có thể theo hoặc bỏ bài.
draw-all-in-unavailable-limit = Tất tay không dùng được vì số chip của bạn vượt quá giới hạn cược hiện tại. Hãy dùng Tố để nhập một mức hợp lệ.
draw-raise-unavailable-cap = Bạn không thể tố vì vòng cược này đã đạt giới hạn số lần tố.
draw-raise-unavailable-limit = Bạn không thể tố đủ mức với số chip và giới hạn cược hiện tại. Bạn có thể theo, bỏ bài, hoặc tất tay khi hành động đó hợp lệ.

draw-current-bet = Mức cược hiện tại trên bàn là { $amount } chip.
draw-raise-range = Mức tố tối thiểu là { $minimum } chip. Sau khi theo, bạn có thể tố thêm tối đa { $maximum } chip.
draw-no-full-raise-available = Bạn cần { $to_call } chip để theo và chỉ còn { $chips } chip, nên không thể tố đủ mức. Bạn có thể theo bằng cách tất tay hoặc bỏ bài.
draw-dealer-unavailable = Ván hiện tại chưa có vị trí người chia bài.
draw-position-unavailable = Bạn không còn trong ván hiện tại nên không có vị trí cược.

draw-card-key = Phím bài { $index }

draw-winner-chips = { $rank }. { $player }: { $chips } chip
