import json
from . import models
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType


class LoginView(APIView):
    # self.dispatch
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        account_obj = models.Account.objects.filter(username=username, password=password).first()
        if account_obj:
            # 用户名密码正确
            tk = token(account_obj.username)
            models.Token.objects.update_or_create(user=account_obj, defaults={
                'token_value': tk
            })
            data = {
                'status': 1000,
                'data': {
                    'username': account_obj.username,
                    'token': tk,
                    'userid': account_obj.pk
                }
            }
            response = HttpResponse(json.dumps(data), status=200)
            response.set_cookie('token_value', tk)
        else:
            data = {
                'status': 1001,
                'error': '用户名或者密码错误'
            }
            response = HttpResponse(json.dumps(data))
        return response

    def options(self, request, *args, **kwargs):
        response = HttpResponse('ok')
        return response


#
class MtoMField(serializers.CharField):
    def get_attribute(self, instance):
       return instance.objects.values('name','title')
    def to_representation(self,value):

        return list(value)

class MyField(serializers.CharField):
    def get_attribute(self, instance):
        #instance 是数据库对应的每行数据，即model 实例对象
        data_list = instance.recommend_courses.all()
        return data_list

    def to_representation(self, value):
        ret = []
        for row in value:
            ret.append({'id': row.id, 'name': row.name})
        return ret


class CourseSerializer(serializers.Serializer):
    '''课程'''
    level_name = serializers.CharField(source='get_level_display')
    id = serializers.IntegerField()
    name = serializers.CharField()
    brief = serializers.CharField()


class CourseDetailSerializer(serializers.ModelSerializer):
    """课程详情"""
    course_name = serializers.CharField(source='course.name')
    recommend_courses = serializers.SerializerMethodField()
    price_policy = serializers.SerializerMethodField()
    chapters = serializers.SerializerMethodField()
    teachers = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()
    user_reviews = serializers.SerializerMethodField()

    class Meta:
        model = models.CourseDetail
        fields = ['id', 'course_name', 'hours', 'why_study', 'what_to_study_brief',
                  'career_improvement', 'prerequisite', 'recommend_courses', 'price_policy',
                  'teachers', 'chapters', 'user_reviews', 'questions']

    def get_recommend_courses(self, obj):
        """获取推荐课程"""
        ret = []
        recommend_courses_list = obj.recommend_courses.all()
        for item in recommend_courses_list:
            ret.append({'id': item.id, 'name': item.name})
        return ret

    def get_price_policy(self, obj):
        """获取价格策略"""
        ret = []
        price_policy = obj.course.price_policy.all()
        for item in price_policy:
            ret.append({'price_policy_id':item.id , 'valid_period': item.get_valid_period_display(), 'price': item.price})
        return ret

    def get_chapters(self, obj):
        """获取章节信息"""
        ret = []
        chapters = obj.course.coursechapters.all()
        print('章节信息是', chapters)
        for item in chapters:
            # chapter: 第几章； name: 章节名字
            ret.append({'chapter': item.chapter, 'name': item.name})
        return ret

    def get_teachers(self, obj):
        """获取教师"""
        ret = []
        teachers = obj.teachers.all()
        for item in teachers:
            ret.append({'name': item.name, 'image': item.image, 'brief': item.brief})
        return ret

    def get_user_reviews(self, obj):
        """
        获取用户评价:
        CourseReview O2O --> EnrolledCourse O2O --》order_detail (订单购买后支持 课程评价) --> ... 获取用户比较困难
                                            FK --》 Course 
        """
        ret = []
        enrolledcourse_list = obj.course.enrolledcourse_set.all()  # 已报名课程
        for item in enrolledcourse_list:
            review_obj = item.coursereview
            ret.append({'review': item.review, 'date': item.date})
        return ret

    def get_questions(self, obj):
        """获取常见问题"""
        ret = []
        content = ContentType.objects.filter(app_label='monkey', model='course').first()
        questions = models.OftenAskedQuestion.objects.filter(content_type=content, object_id=obj.course.pk).all()
        for item in questions:
            ret.append({'question': item.question, 'answer': item.answer})
        return ret


class CoursesView(APIView):
    def get(self, request, *args, **kwargs):
        response = {'code': 1000, 'msg': None, 'data': None}

        try:
            pk = self.kwargs.get('pk', None)
            if pk:
                course_obj = models.CourseDetail.objects.get(course=pk)
                ser = CourseDetailSerializer(instance=course_obj, many=False)
                print(ser.data)
            else:
                # 排除学位课程
                course_ls = models.Course.objects.exclude(course_type=2)
                ser = CourseSerializer(instance=course_ls, many=True)
            response['data'] = ser.data
        except Exception as e:
            response['code'] = 1001
            response['msg'] = 'something wrong...'

        return Response(response)


class PaymentHandleView(APIView):
    def post(self, request, *args, **kwargs):
        """
        收到前端传来的数据 {{'course_id': 1, plicy_id: 1}, {}}
        检查课程是否合法（1.存在 2.课程状态），价格策略是否合法（1.存在 2.和该课程关联）
        保存结算数据到redis: 用户id: {policy_id: {xxx}}
        """
        from Service.redis_service import SingleRedis
        redis = SingleRedis()

        response = {'code': 1000,  # code: 1000 成功；
               'msg': None,
               'data': None}

        data = json.loads(request.body.decode('utf-8'))
        print(data)

        # 验证数据
        for item in data:
            course_id = item.get('course_id')
            course_obj = models.Course.objects.filter(id=course_id).first()
            if not course_obj:
                response['code'] = 1001
                response['msg'] = '选择的课程不存在！'
                return Response(response)

            if course_obj.status != 0:
                response['code'] = 1002
                response['msg'] = '选择的课程暂时无法购买！'
                return Response(response)

            price_policy_id = int(item.get('price_policy_id'))
            price_policy_obj = models.PricePolicy.objects.filter(id=price_policy_id).first()
            if not price_policy_obj:
                response['code'] = 1003
                response['msg'] = '选择的价格策略不存在！'
                return Response(response)

            print('当前优惠券绑定商品是：',price_policy_obj.content_object)
            if price_policy_obj.content_object != course_obj:
                response['code'] = 1004
                response['msg'] = '选择的价格策略和课程不匹配！'
                return Response(response)

            # 课程和价格策略验证没问题，创建数据准备存入redis
            detail = {
                'price': price_policy_obj.price,
                'valid_period': price_policy_obj.get_valid_period_display(),
                'course': {
                    'id': course_obj.id,
                    'name': course_obj.name,
                    'course_img': course_obj.course_img
                }
            }

            try:
                redis.conn.hset(request.user.id, price_policy_id, json.dumps(detail))
            except Exception as e:
                response['code'] = 1005
                response['msg'] = '无法获取用户信息，请先登录！'

        return Response(response)

    def get(self, request, *args, **kwargs):
        """
        从redis获取结算列表；
        获取当前用户所有可用优惠券（排除过期的，已经使用的）
        :param request: 
        :param args: 
        :param kwargs: 
        :return: 
        """
        pass



















