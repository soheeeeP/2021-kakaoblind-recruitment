import uuid

from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from kakaoblind2021 import settings
from kakaoT.models import Problem, Location, Truck


class StartView(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        req_token = request.META.get('HTTP_X_AUTH_TOKEN')
        if req_token != getattr(settings, 'X_AUTH_TOKEN'):
            message = "INVALID X_AUTH_TOKEN ERROR"
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        idx = request.query_params.get('problem')
        scenario = getattr(settings, 'problem')[idx]

        try:
            # 다시 같은 시나리오를 simulate하는 경우
            p = Problem.objects.prefetch_related('location_set', 'truck_set').get(idx=idx)
            # 새로운 auth_key 발급
            p.auth_key = uuid.uuid4()

            # Problem을 참조하고 있는 Place와 Truck object 삭제
            p.location_set.all().delete()
            p.truck_set.all().delete()
            p.save()

        except Problem.DoesNotExist:
            # 새로운 시나리오를 simulate하는 경우
            with transaction.atomic():
                # Problem 시나리오 생성
                p = Problem.objects.create(
                    idx=idx,
                    auth_key=uuid.uuid4()
                )

                # 대여소 생성 (row, col, id, 자전거 대수)
                size = scenario['size']
                bike = scenario['bike'] / (size ** 2)
                idx = 0
                for i in range(1, size + 1, 1):
                    for j in range(size, 0, -1):
                        Location.objects.create(
                            problem_id=p.id,
                            idx=idx,
                            row=i,
                            col=j,
                            bike=bike
                        )
                        idx += 1

                # 트럭 생성 (시작 위치 [0,0])
                truck = scenario['truck']
                idx = 0
                for i in range(truck):
                    Truck.objects.create(
                        problem_id=p.id,
                        idx=idx
                    )
                    idx += 1
        finally:
            response = {
                "auth_key": p.auth_key,
                "problem": p.idx,
                "time": 0
            }
            return Response(response, status=status.HTTP_201_CREATED)
