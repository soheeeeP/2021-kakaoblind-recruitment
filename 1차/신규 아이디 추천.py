# https://programmers.co.kr/learn/courses/30/lessons/72410
# 2021 KAKAO BLIND RECRUITMENT 신규 아이디 추천

import re


def solution(new_id):
    _new_id = re.findall(r"[\w_\-.]", new_id.lower())
    answer = []
    for x in _new_id:
        if len(answer) > 0 and answer[-1] == '.' and x == '.':
            continue
        else:
            answer.append(x)

    if len(answer) > 0 and answer[0] == '.':
        answer.pop(0)
    if len(answer) > 0 and answer[-1] == '.':
        answer.pop(-1)
    if len(answer) == 0:
        answer.append('a')
    if len(answer) >= 16:
        answer = answer[0:15]
        if answer[-1] == '.':
            answer.pop(-1)
    if len(answer) <= 2:
        while len(answer) < 3:
            answer.append(answer[-1])

    x = ''.join(answer)
    print(x)
    return x


if __name__ == '__main__':
    solution("...!@BaT#*..y.abcdefghijklm")
    solution("z-+.^.")
    solution("=.=")
    solution("123_.def")
    solution("abcdefghijklmn.p")
