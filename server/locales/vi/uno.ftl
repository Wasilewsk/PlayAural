# Vietnamese translations for UNO.
# NOTE: agent-authored, provisional — needs native-speaker review.

game-name-uno = UNO

# Colors
uno-color-red = Đỏ
uno-color-yellow = Vàng
uno-color-green = Xanh lá
uno-color-blue = Xanh dương
uno-color-wild = Đổi màu

# Card names
uno-card-number = { $color } { $value }
uno-card-skip = { $color } Mất lượt
uno-card-reverse = { $color } Đảo chiều
uno-card-draw-two = { $color } Rút Hai
uno-card-wild = Đổi màu
uno-card-wild-four = Đổi màu Rút Bốn

# Options
uno-set-winning-score = Giới hạn điểm: { $score }
uno-enter-winning-score = Nhập giới hạn điểm
uno-option-changed-winning-score = Giới hạn điểm đã được đặt là { $score }.

uno-set-scoring-mode = Cách tính điểm: { $mode }
uno-select-scoring-mode = Chọn cách tính điểm
uno-option-changed-scoring-mode = Cách tính điểm đã được đặt là { $mode }.
uno-scoring-first = Ai đạt giới hạn trước thì thắng
uno-scoring-elimination = Loại trực tiếp

uno-set-skip-after-draw = Hình phạt rút bài làm mất lượt: { $enabled }
uno-option-changed-skip-after-draw = Hình phạt rút bài làm mất lượt { $enabled }.

uno-set-responses = Chồng lá rút: { $enabled }
uno-option-changed-responses = Chồng lá rút { $enabled }.

uno-set-advanced-responses = Phản đòn nâng cao: { $enabled }
uno-option-changed-advanced-responses = Phản đòn nâng cao { $enabled }.

uno-set-wait-for-draw-responses = Chờ phản đòn khi hết bài: { $enabled }
uno-option-changed-wait-for-draw-responses = Chờ phản đòn khi hết bài { $enabled }.

uno-set-bluff = Thách thức Đổi màu Rút Bốn: { $enabled }
uno-option-changed-bluff = Thách thức Đổi màu Rút Bốn { $enabled }.

uno-set-straights = Đánh liên tiếp: { $enabled }
uno-option-changed-straights = Đánh liên tiếp { $enabled }.

uno-set-interceptions = Cướp lượt: { $enabled }
uno-option-changed-interceptions = Cướp lượt { $enabled }.

uno-set-super-interceptions = Cướp lượt nâng cao: { $enabled }
uno-option-changed-super-interceptions = Cướp lượt nâng cao { $enabled }.

uno-set-zero-seven = Luật số 0 và 7: { $enabled }
uno-option-changed-zero-seven = Luật số 0 và 7 { $enabled }.

uno-set-free-draws = Số lần rút tự do mỗi lượt: { $count }
uno-enter-free-draws = Nhập số lần rút tự do mỗi lượt
uno-option-changed-free-draws = Số lần rút tự do mỗi lượt đã được đặt là { $count }.

# Option validation
uno-error-advanced-responses-require-responses = Muốn bật Phản đòn nâng cao thì trước hết phải bật Chồng lá rút.
uno-error-wait-responses-require-responses = Muốn bật Chờ phản đòn khi hết bài thì trước hết phải bật Chồng lá rút.
uno-error-super-interceptions-require-interceptions = Muốn bật Cướp lượt nâng cao thì trước hết phải bật Cướp lượt.

# Actions
uno-draw = Rút bài
uno-say-uno = UNO
uno-read-top = Đọc lá bài trên cùng
uno-read-color = Đọc màu hiện tại
uno-read-counts = Đọc số lượng bài
uno-read-hand = Đọc giá trị bài trên tay
uno-sort-color = Sắp xếp theo màu
uno-sort-number = Sắp xếp theo số

# Gameplay announcements
uno-new-hand = Vòng { $round }.
uno-start-card = { $player } lật lá { $card }.
uno-current-color = Màu hiện tại: { $color }.
uno-dealt-cards = Mỗi người được chia { $cards } lá bài.
uno-direction-reversed = Hướng chơi đã bị đảo chiều.
uno-player-plays = { $player } đánh { $card }.
uno-you-play = Bạn đánh { $card }.
uno-color-chosen = Màu bây giờ là { $color }.
uno-player-draws-one = { $player } rút một lá bài.
uno-player-draws-many = { $player } rút { $count } lá bài.
uno-you-draw-one = Bạn rút một lá bài.
uno-you-draw-many = Bạn rút { $count } lá bài.
uno-cant-play = { $player } không đánh được.
uno-you-cant-play = Bạn không đánh được.
uno-you-skipped = Bạn bị mất lượt.
uno-says-uno = { $player } hô UNO!
uno-you-say-uno = Bạn hô UNO!
uno-callout = { $caller } bắt lỗi { $player } vì không hô UNO! { $player } rút { $count } lá.
uno-you-callout = Bạn bắt lỗi { $player } vì không hô UNO! { $player } rút { $count } lá.
uno-callout-you = { $caller } bắt lỗi bạn vì không hô UNO! Bạn rút { $count } lá.
uno-cannot-play-that = Bạn không thể đánh { $card }. { $reason }
uno-reshuffle = Đang xáo lại chồng bài đã đánh.
uno-hand-blocked = Không ai đánh được. Vòng này kết thúc.
uno-error-choose-color-first = Hãy chọn màu cho lá Đổi màu trước khi đánh lá khác.
uno-error-wait-color-choice = Hãy chờ người vừa đánh lá Đổi màu chọn màu trước khi đánh tiếp.
uno-error-wild-transition = Hãy chờ màu vừa chọn có hiệu lực rồi mới đánh lá tiếp theo.
uno-error-choose-swap-first = Hãy chọn người để đổi bài, hoặc từ chối, trước khi làm hành động khác.
uno-error-wait-swap-choice = Hãy chờ lựa chọn đổi bài của lá số 7 kết thúc trước khi đánh tiếp.
uno-error-wait-next-hand = Hãy chờ vòng tiếp theo bắt đầu rồi mới đánh bài.
uno-error-wait-intro = Hãy chờ phần chuẩn bị vòng chơi kết thúc rồi mới đánh bài.
uno-reason-draw-stack-response = Bạn đang chịu chồng lá rút { $count } lá; hãy đánh một lá phản đòn hợp lệ hoặc rút hình phạt.
uno-reason-draw-stack-no-response = Bạn đang chịu hình phạt rút { $count } lá, và Chồng lá rút đang tắt; hãy rút hình phạt.
uno-reason-match-required = Lá trên cùng là { $top }, màu hiện tại là { $color }; hãy đánh đúng màu, đúng số hoặc biểu tượng chức năng, hoặc đánh một lá Đổi màu.
uno-reason-card-not-available = Lá này không dùng được trong trạng thái hiện tại.

# Bluff challenge
uno-bluff-challenge = Thách thức Đổi màu Rút Bốn
uno-bluff-caught = { $player } đã đánh lá Đổi màu Rút Bốn không hợp lệ và phải rút { $count } lá!
uno-you-bluff-caught = Bạn đã đánh lá Đổi màu Rút Bốn không hợp lệ và phải rút { $count } lá!
uno-bluff-wrong = { $player } thách thức lá Đổi màu Rút Bốn sai và phải rút { $count } lá!
uno-you-bluff-wrong = Bạn thách thức lá Đổi màu Rút Bốn sai và phải rút { $count } lá!

# Zero / seven rule
uno-rotate-hands = Mọi người chuyền bài trên tay!
uno-swap-hands = { $player } đổi bài với { $target }!
uno-you-swap = Bạn đổi bài với { $target }!
uno-swap-with-you = { $player } đổi bài với bạn!
uno-swap-with = Đổi bài với { $player }
uno-choose-swap = Chọn người để đổi bài, hoặc từ chối.
uno-swap-none = Không đổi
uno-you-swap-none = Bạn giữ nguyên bài của mình.
uno-swap-none-other = { $player } giữ nguyên bài của mình.

# Interceptions / straights
uno-player-intercepts = { $player } cướp lượt bằng { $card }!
uno-you-intercept = Bạn cướp lượt bằng { $card }!
uno-bad-intercept = Đó không phải cú cướp lượt hợp lệ. Bị phạt ba điểm.
uno-not-your-turn = Chưa tới lượt bạn.

# Info
uno-no-top = Chưa có lá bài trên cùng.
uno-top-card = { $card }.
uno-color-is = { $color }.
uno-deck-count = bộ bài { $count }
uno-sorting-color = Sắp xếp theo màu.
uno-sorting-number = Sắp xếp theo số.

# Round / game end
uno-round-winner = { $player } thắng vòng này!
uno-you-win-round = Bạn thắng vòng này!
uno-round-points-from = { $points } từ { $player }
uno-round-details-none = Không lấy được điểm nào từ đối thủ.
uno-round-summary = { $details }. { $player } nhận được { $total }.
uno-round-summary-you = { $details }. Bạn nhận được { $total }.
uno-you-add-penalty-points = Bạn bị cộng { $points } điểm phạt vào tổng điểm sau vòng này.
uno-player-adds-penalty-points = { $player } bị cộng { $points } điểm phạt vào tổng điểm sau vòng này.
uno-you-are-eliminated = Bạn đã chạm mức loại { $limit } điểm và phải rời ván.
uno-player-is-eliminated = { $player } đã chạm mức loại { $limit } điểm và phải rời ván.
uno-you-win-game =
    { $mode ->
        [elimination] Bạn là người cuối cùng còn lại và thắng với { $score } điểm phạt.
       *[first_to_limit] Bạn thắng cả ván với { $score } điểm!
    }
uno-player-wins-game =
    { $mode ->
        [elimination] { $player } là người cuối cùng còn lại và thắng với { $score } điểm phạt.
       *[first_to_limit] { $player } thắng cả ván với { $score } điểm!
    }
uno-game-tie = Tất cả đều bị loại. Ván đấu hòa!
uno-line-format = { $rank }. { $player }: { $score }

# Hand value (phím d)
uno-read-hand-value = { $count } lá, trị giá { $points } điểm.
