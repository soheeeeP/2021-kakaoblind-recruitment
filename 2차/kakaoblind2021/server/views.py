import json
import typing

import requests

from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from kakaoT.models import Problem, Location
from kakaoblind2021 import settings
from utils.scheduler import KakaoTScheduler, SERVER_STATUS


class SimulateView(generics.CreateAPIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://grepp-cloudfront.s3.ap-northeast-2.amazonaws.com/programmers_imgs/competition-imgs/2021kakao/problem"

    def create_truck_dummy_data(self, p) -> typing.Optional[Problem]:
        import uuid
        truck_problem = Problem.objects.create(idx=3, auth_key=uuid.uuid4())
        loc_values = p.location_set.all().values('idx', 'row', 'col', 'bike')
        dummy_data = [Location(**values, problem=truck_problem) for values in loc_values]
        Location.objects.bulk_create(dummy_data)

        return truck_problem

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
        test_data = {
          "0": [[3, 0, 10]],
          "1": [[1, 3, 1], [1, 4, 15]],
          "2": [[0, 3, 2], [3, 1, 4], [0, 3, 1]],
          "3": [[1, 3, 5]]
        }

        # 서버(시나리오)의 scheduler에 작업을 추가
        kakao = getattr(settings, 'kakao')
        if kakao.server_status == SERVER_STATUS.finished:
            kakao.termiate_scheduler()
            delattr(settings, 'kakao')
            kakao = KakaoTScheduler()
            setattr(settings, 'kakao', kakao)
            return Response({'message': 'GENERATE NEW AUTH_KEY'}, status=status.HTTP_400_BAD_REQUEST)
        elif kakao.server_status == SERVER_STATUS.in_progress or kakao.server_status == SERVER_STATUS.ready:
            return Response({'message': 'REQUEST IS IN PROGRESS... '}, status=status.HTTP_400_BAD_REQUEST)

        req_url = self.base_url + str(idx) + "_day-1.json"
        req_status = requests.get(req_url).ok
        if req_status:
            rental_req_data = requests.get(req_url).json()
        else:
            rental_req_data = test_data

        kakao.init_scheduler(problem=p, truck_problem=self.create_truck_dummy_data(p=p), scenario=p.idx)
        kakao.add_server_status_scheduler()

        # 자전거 대여 요청 수행
        kakao.add_scheduler(rental=rental_req_data)

        commands = request.POST.get('commands', None)
        if commands:    # 트럭 이동 요청이 들어온 경우
            kakao.add_truck_scheduler(commands=json.loads(commands))

        response = {
            "status": kakao.server_status,
            "time": kakao.truck_runtime,
            "failed_requests_count": kakao.truck_failed_req_count,
            "distance": kakao.actual_truck_movement_dist
        }
        return Response(response, status=status.HTTP_200_OK)
