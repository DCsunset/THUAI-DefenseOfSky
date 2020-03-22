require './tool'

set_participants(
    'su', 1000, '',
    'quq', 1500, '',
    'qvq', 1600, '',
    'qwq', 1700, '',
    'qxq', 1800, ''
)

require './contest'

test_submission(3)
test_timer()
test_timer()
test_timer()
test_manual('1, 2, 3, 4')
test_update_stats('{ "player0": 112, "player1": 20, "replay" }', {1, 2})
test_update_stats('{ "player0": 122, "player1": 20, "replay" }', {1, 3})
test_update_stats('{ "player0": 0, "player1": 0, "replay" }', {2, 4})
test_update_stats('{ "player0": -1, "player1": 2, "replay" }', {1, 2})
test_timer()
