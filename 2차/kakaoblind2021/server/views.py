import json
import requests

from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from kakaoT.models import Problem
from kakaoblind2021 import settings
from utils.scheduler import KakaoTScheduler, SERVER_STATUS


class SimulateView(generics.CreateAPIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://grepp-cloudfront.s3.ap-northeast-2.amazonaws.com/programmers_imgs/competition-imgs/2021kakao/problem"

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        auth_key = request.META.get('HTTP_AUTHORIZATION')
        try:
            p = Problem.objects.prefetch_related('location_set', 'truck_set').get(auth_key=auth_key)
            idx = p.idx
        except Problem.DoesNotExist:
            message = "INVALID AUTH_KEY ERROR"
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        # 테스트용 데이터 (problem 0)
        # test_data = {
        #   "0": [[3, 0, 10]],
        #   "1": [[1, 3, 1], [1, 4, 15]],
        #   "2": [[0, 3, 2], [3, 1, 4], [0, 3, 1]],
        #   "3": [[1, 3, 5]]
        # }

        # 서버(시나리오)의 scheduler에 작업을 추가
        kakao = getattr(settings, 'kakao')
        print(kakao.server_status)
        if kakao.server_status == SERVER_STATUS.initial:
            kakao.init_scheduler(scenario=p.idx)
        elif kakao.server_status == SERVER_STATUS.finished:
            kakao.termiate_scheduler()
            delattr(settings, 'kakao')
            kakao = KakaoTScheduler()
            setattr(settings, 'kakao', kakao)
            kakao.init_scheduler(scenario=p.idx)

        req_url = self.base_url + str(idx) + "_day-1.json"
        rental_req_data = requests.get(req_url).json()

        # 자전거 대여 요청 수행
        kakao.add_bike_scheduler(problem=p, rental=rental_req_data)
        kakao.set_server_scenario_score()

        commands = request.POST.get('commands', None)
        if commands:    # 트럭 이동 요청이 들어온 경우
            kakao.add_truck_scheduler(commands=json.loads(commands))

        response = {
            "status": kakao.server_status,
            "time": kakao.runtime,
            "failed_requests_count": kakao.failed_bike_req_count + kakao.failed_truck_req_count,
            "distance": kakao.truck_movement_dist / 1000
        }
        return Response(response, status=status.HTTP_200_OK)
