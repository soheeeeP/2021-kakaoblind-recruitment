# https://programmers.co.kr/learn/courses/30/lessons/72414
# 2021 KAKAO BLIND RECRUITMENT 광고 삽입

def sec_t(h, m, s):
    return h * 3600 + m * 60 + s


def solution(play_time, adv_time, logs):
    if play_time == adv_time:
        return "00:00:00"

    play_time_hms = list(map(int, play_time.split(":")))
    play = [0] * (sec_t(play_time_hms[0], play_time_hms[1], play_time_hms[2]) + 1)
    adv_time_hms = list(map(int, adv_time.split(":")))
    adv_len = sec_t(adv_time_hms[0], adv_time_hms[1], adv_time_hms[2])      # 슬라이딩 윈도우의 크기

    # for l in logs:
    #     s, e = l.split("-")
    #     start_h, start_m, start_sec = list(map(int, s.split(":")))
    #     end_h, end_m, end_sec = list(map(int, e.split(":")))
    #
    #     # 시간복잡도 O(MN)으로 시간 초과가 발생하
    #     for x in range(sec_t(start_h, start_m, start_sec), sec_t(end_h, end_m, end_sec)):
    #         play[x] += 1

    _logs = []
    for l in logs:
        s, e = l.split("-")
        start_h, start_m, start_sec = list(map(int, s.split(":")))
        end_h, end_m, end_sec = list(map(int, e.split(":")))
        _logs.append([sec_t(start_h, start_m, start_sec), sec_t(end_h, end_m, end_sec)])

    dp = [0] * 360001
    for i in range(len(_logs)):
        dp[_logs[i][0]] += 1
        dp[_logs[i][1]] -= 1

    val = 0
    for i in range(1, len(play)):
        val += dp[i]
        play[i] += val

    # 광고가 0초에서 시작하는 경우부터 계산
    cnt = sum(play[0:adv_len])
    max_cnt = cnt
    adv_start = 0
    for i in range(1, len(play) - adv_len):
        cnt -= play[i - 1]
        cnt += play[i + adv_len - 1]
        if cnt > max_cnt:
            max_cnt = cnt
            adv_start = i

    hour = adv_start // 3600
    adv_start %= 3600
    minute = adv_start // 60
    second = adv_start % 60

    result = f'{str(hour).zfill(2)}:{str(minute).zfill(2)}:{str(second).zfill(2)}'
    print(result)
    return result


if __name__ == '__main__':
    solution("50:00:00", "50:00:00", ["15:36:51-38:21:49", "10:14:18-15:36:51", "38:21:49-42:51:45"])
    solution("02:03:55", "00:14:15",
             ["01:20:15-01:45:14", "00:40:31-01:00:00", "00:25:50-00:48:29", "01:30:59-01:53:29", "01:37:44-02:02:30"])
    solution("99:59:59", "25:00:00",
             ["69:59:59-89:59:59", "01:00:00-21:00:00", "79:59:59-99:59:59", "11:00:00-31:00:00"])
