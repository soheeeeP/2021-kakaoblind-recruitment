import requests
import time

from apscheduler.schedulers.background import BackgroundScheduler
from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from kakaoT.models import Problem


class KakaoTScheduler(object):
    def __init__(self, problem, rental):
        self.problem = problem
        self.runtime = 0
        self.rental = rental  # 자전거 대여 요청 처리 대기열
        self.back = {}  # 자전거 반납 처리 대기열
        self.total_req_count = 0  # 전체 요청
        self.failed_req_count = 0  # 실패 요청
        self.scheduler = BackgroundScheduler()

    def __del__(self):
        self.terminate_scheduler()

    def terminate_scheduler(self):
        self.scheduler.shutdown()

    def init_scheduler(self):
        print(self.rental)
        self.scheduler.start()
        self.scheduler.add_job(self.bike_scheduler, "cron", second="*/5", id="bike")
        # self.scheduler.add_job(self.truck_scheduler, "cron", minute="*/1", id="truck")

    # db에 수정사항이 반영되지가 않음
    def bike_scheduler(self):
        loc_set = self.problem.location_set.all()

        print("============ BIKE SCHEDULER ============")
        print('서버시간: ' + str(self.runtime))

        print('대여소 현황: ', end='')
        for x in loc_set:
            print(x.bike, end=' ')
        print()

        print('반납 처리 대기열: ', end='')
        print(self.back)

        # 현재 시간에 예정되어 있는 자전거 반납 처리
        if self.runtime in self.back:
            back_idx = self.back[self.runtime]
            for b in back_idx:
                loc = loc_set.get(idx=b)
                loc.bike += 1  # 반납할 대여소에 자전거 반납
                loc.save()
            # 반납 대기열에서 제거
            self.back.pop(self.runtime)

        if str(self.runtime) in self.rental:
            data = self.rental[str(self.runtime)]
            print('처리할 요청: ', end='')
            print(data)

            # 자전거 대여 요청 처리
            for d in data:
                self.total_req_count += 1
                # [자전거를 대여할 대여소 ID, 자전거를 반납할 대여소 ID, 이용시간(분)]
                loc = loc_set.get(idx=d[0])

                # 대여소에 자전거가 남아있지 않는 경우, 요청 실패 처리
                if loc.bike < 1:
                    self.failed_req_count += 1
                # 대여소에 자전거가 1대 이상 남아있는 경우, 자전거 대여
                else:
                    loc.bike -= 1
                    loc.save()

                    # 반납시간 계산
                    return_time = self.runtime + d[2]
                    print(f'ID {loc.idx}에서 자전거 대여. {return_time}분에 ID {d[1]}인 자전거 대여소에 반납 예정')
                    print(f'ID {loc.idx}에는 자전거 {loc.bike}대가 남음')
                    # 자전거 반납 대기열에 추가
                    if return_time not in self.back:
                        self.back[return_time] = [d[1]]
                    else:
                        self.back[return_time].append(d[1])
        print('취소된 요청 수: ' + str(self.failed_req_count))

        # 서버 실행 시간 업데이트
        self.runtime += 1

        # 서버가 수행한 simulate 요청이 720번 성공한 경우, 서버의 상태를 'finished'로 변경, 점수 계산
        # (total_req_count - failed_req_count)
        print("bike:" + time.ctime())

    def truck_scheduler(self):
        print("truck:" + time.ctime())


class SimulateView(generics.CreateAPIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://grepp-cloudfront.s3.ap-northeast-2.amazonaws.com/programmers_imgs/competition-imgs/2021kakao/problem"

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        auth_key = request.META.get('HTTP_AUTHORIZATION')
        try:
            p = Problem.objects.prefetch_related('location_set').get(auth_key=auth_key)
            idx = p.idx
        except Problem.DoesNotExist:
            message = "INVALID AUTH_KEY ERROR"
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        test_data = {"0": [[3, 0, 10]],
                     "1": [[1, 3, 1], [1, 4, 15]],
                     "2": [[0, 3, 2], [3, 1, 4], [0, 3, 1]],
                     "3": [[1, 3, 5]]
                     }

        req_url = self.base_url + str(idx) + "_day-1.json"
        rental_req_data = requests.get(req_url).json()

        kakao = KakaoTScheduler(problem=p, rental=rental_req_data)
        transaction.on_commit(lambda: kakao.init_scheduler())

        return Response()
