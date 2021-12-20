# https://programmers.co.kr/learn/courses/30/lessons/72411
# 2021 KAKAO BLIND RECRUITMENT 메뉴 리뉴얼

def solution(orders, course):
    result = []

    import itertools
    for c in course:
        menu = {}
        for order in orders:
            data = list(''.join(sorted(x)) for x in itertools.combinations(order, c))
            for d in data:
                if d in menu:
                    menu[d] += 1
                else:
                    menu[d] = 1
        if len(menu) == 0:
            continue
        value = max(menu.values())
        if value == 1:
            continue
        for k, v in menu.items():
            if v == value:
                result.append(k)

    result.sort()
    return result


if __name__ == '__main__':
    solution(["ABCFG", "AC", "CDE", "ACDE", "BCFG", "ACDEH"], [2, 3, 4])
    solution(["ABCDE", "AB", "CD", "ADE", "XYZ", "XYZ", "ACD"], [2, 3, 5])
    solution(["XYZ", "XWY", "WXA"], [2, 3, 4])
