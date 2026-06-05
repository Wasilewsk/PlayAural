# Bản địa hóa Humanity Cards (Bài Phản Nhân Loại)

# Tùy chọn
hc-set-winning-score = Điểm để thắng: { $score }
hc-desc-winning-score = Số điểm cần để giành chiến thắng
hc-enter-winning-score = Nhập điểm để thắng:
hc-option-changed-winning-score = Điểm để thắng đã đặt thành { $score }.

hc-set-hand-size = Số bài trên tay: { $count }
hc-desc-hand-size = Số lá bài trên tay
hc-enter-hand-size = Nhập số bài trên tay:
hc-option-changed-hand-size = Số bài trên tay đã đặt thành { $count }.

hc-set-card-packs = Bộ bài (đã chọn { $count } trên { $total })
hc-desc-card-packs = Chọn bộ bài sẽ dùng
hc-option-changed-card-packs = Đã thay đổi lựa chọn bộ bài.

hc-set-czar-selection = Cách chọn Trọng Tài: { $mode }
hc-select-czar-selection = Chọn cách chỉ định Trọng Tài
hc-option-changed-czar-selection = Cách chọn Trọng Tài đã đặt thành { $mode }.

hc-set-num-judges = Số trọng tài: { $count }
hc-enter-num-judges = Nhập số trọng tài:
hc-option-changed-num-judges = Số trọng tài đã đặt thành { $count }.

hc-czar-rotating = Luân phiên
hc-czar-random = Ngẫu nhiên
hc-czar-winner = Người thắng gần nhất

# Diễn biến trò chơi
hc-game-starting = Đang xáo bài...
hc-dealing-cards = Chia { $count } lá bài cho mỗi người chơi.
hc-round-start = Vòng { $round }.

# Thông báo trọng tài
hc-judge-is = { $player } { $count ->
    [one] là Trọng Tài
   *[other] và { $others } là các Trọng Tài
}.
hc-you-are-judge = Bạn là Trọng Tài vòng này.
hc-you-are-not-judge = Bạn không phải Trọng Tài vòng này.

# Lá bài đen
hc-black-card = Câu hỏi là: { $text }
hc-black-card-pick = Chọn { $count } lá.
hc-view-black-card = Xem lá bài câu hỏi

# Giai đoạn nộp bài
hc-select-cards = Chọn { $count } { $count ->
    [one] lá bài
   *[other] lá bài
} từ tay bạn.
hc-card-selected = { $text }, đã chọn
hc-card-not-selected = { $text }
hc-submit-cards = Nộp bài (đã chọn { $selected } trên { $required })
hc-submitted = Bạn đã nộp bài.
hc-player-submitted = { $player } đã nộp bài.
hc-submission-progress = { $submitted } trên { $total } người chơi đã nộp bài.
hc-waiting-for-submissions = Đang chờ mọi người nộp bài...
hc-already-submitted = Bạn đã nộp bài rồi.
hc-wrong-card-count = Bạn cần chọn đúng { $count } { $count ->
    [one] lá bài
   *[other] lá bài
}.

# Giai đoạn chấm bài
hc-judging-start = Đã đủ bài! Đến lúc chấm.
hc-select-winner-prompt = Chọn bài thắng cuộc
hc-submission-option = { $text }

# Kết quả
hc-winner-announcement = { $player } thắng vòng này! Điểm: { $score }.
hc-winner-card = Câu trả lời thắng cuộc: { $text }
hc-round-scores = Điểm sau vòng { $round }:
hc-score-line = { $player }: { $score } { $score ->
    [one] điểm
   *[other] điểm
}
hc-all-submissions = Các bài khác:
hc-submission-reveal = { $player }: { $text }

# Xem
hc-preview-submission = Xem trước bài nộp của bạn
hc-view-submission = Xem bài nộp của bạn
hc-preview-submission-text = Xem trước: { $text }
hc-your-submission = Bài nộp của bạn: { $text }
hc-select-cards-first = Hãy chọn ít nhất 1 lá bài trước.

# Chiến thắng
hc-game-winner = { $player } thắng với { $score } điểm!
hc-you-win = Bạn thắng với { $score } điểm!

# Quản lý bộ bài
hc-deck-reshuffled = Chồng bài trắng đã bỏ được xáo lại vào bộ bài.
hc-black-deck-reshuffled = Chồng bài đen đã bỏ được xáo lại vào bộ bài.
hc-not-enough-cards = Không đủ bài. Hãy thử bật thêm bộ bài.

# Quản lý bài trên tay
hc-view-hand = Xem bài trên tay

# Điểm số
hc-view-scores = Xem điểm
hc-no-scores = Chưa có điểm.

# Lượt của ai / trọng tài là ai
hc-whose-judge = Ai đang làm trọng tài
hc-waiting-for = Đang chờ { $names } nộp bài.
hc-all-submitted-waiting-judge = Tất cả người chơi đã nộp bài. Đang chờ { $judge } chấm bài.
