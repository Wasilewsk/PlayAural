# Bản địa hóa Senet

game-name-senet = Senet

# Bắt đầu trò chơi
senet-game-started = { $p1 } là người chơi 1, { $p2 } là người chơi 2. { $first } đi trước.

# Tung que
senet-throw = { $player } tung được { $result }.{ $bonus ->
    [yes] {" "}Tung thêm!
   *[no] {""}
}

# Di chuyển
senet-move-you = Bạn di chuyển từ ô { $from } đến ô { $to }.
senet-move-other = { $player } di chuyển từ ô { $from } đến ô { $to }.
senet-swap-you = Bạn đổi chỗ với { $opponent } tại ô { $to }. { $opponent } lui về ô { $from }.
senet-swap-other = { $player } đổi chỗ với { $opponent } tại ô { $to }. { $opponent } lui về ô { $from }.
senet-bearoff-you = Bạn đưa quân ra ngoài từ ô { $from }. Còn lại { $remaining } quân.
senet-bearoff-other = { $player } đưa quân ra ngoài từ ô { $from }. Còn lại { $remaining } quân.
senet-water-you = Bạn rơi vào Ngôi Nhà Nước! Quân bị đưa đến ô { $dest }.
senet-water-other = { $player } rơi vào Ngôi Nhà Nước! Quân bị đưa đến ô { $dest }.
senet-happiness-you = Bạn đã đến Ngôi Nhà Hạnh Phúc.
senet-happiness-other = { $player } đã đến Ngôi Nhà Hạnh Phúc.

# Không có nước đi
senet-no-moves-you = Bạn không có nước đi hợp lệ.
senet-no-moves-other = { $player } không có nước đi hợp lệ.

# Nhãn ô
senet-sq-empty = { $sq }
senet-sq-own = { $sq }, quân của bạn
senet-sq-opponent = { $sq }, { $owner }
senet-sq-empty-special = { $sq }, { $name }
senet-sq-own-special = { $sq }, { $name }, quân của bạn
senet-sq-opponent-special = { $sq }, { $name }, { $owner }

# Tên ô đặc biệt
senet-house-rebirth = Tái Sinh
senet-house-happiness = Hạnh Phúc
senet-house-water = Nước
senet-house-three-truths = Ba Sự Thật
senet-house-re-atum = Re-Atum

# Trạng thái
senet-status = { $p1 }: { $off1 } quân ra. { $p2 }: { $off2 } quân ra.{ $phase ->
    [throwing] {" "}Đang chờ tung.
   *[moving] {" "}Kết quả: { $roll }.
}
senet-sticks = { $result }
senet-sticks-none = Chưa tung.

# Chiến thắng
senet-wins = { $player } thắng! Tất cả quân đã ra ngoài.

# Nhãn hành động
senet-check-status = Trạng thái
senet-check-sticks = Kết quả que
senet-check-score = Điểm số
senet-score = { $p1 }: { $off1 } quân. { $p2 }: { $off2 } quân.

# Lỗi
senet-not-your-piece = Đây không phải quân của bạn.
senet-no-piece-there = Không có quân tại ô này.
senet-no-moves-from-here = Không có nước đi hợp lệ từ ô này.

# Tùy chọn
senet-option-bot-difficulty = Độ khó bot: { $bot_difficulty }
senet-option-select-bot-difficulty = Chọn độ khó bot
senet-option-changed-bot-difficulty = Độ khó bot đã được đặt thành { $bot_difficulty }.
senet-difficulty-random = Ngẫu nhiên
senet-difficulty-simple = Đơn giản
