import json
from . import models
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from monkey.utils.authentication import token, CustomAuthentication
from django.contrib.contenttypes.models import ContentType
from Service.redis_service import SingleRedis #Redis

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
            ret.append({'valid_period': item.get_valid_period_display(), 'price': item.price})
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
    authentication_classes = [CustomAuthentication]
    def get(self, request, *args, **kwargs):
        response = {'code': 1000, 'msg': None, 'data': None}

        try:
            pk = self.kwargs.get('pk', None)
            if pk:
                course_obj = models.CourseDetail.objects.get(course=pk)
                ser = CourseDetailSerializer(instance=course_obj, many=False)
                print(ser.data)
            else:
                course_ls = models.Course.objects.all()
                ser = CourseSerializer(instance=course_ls, many=True)
            response['data'] = ser.data
        except Exception as e:
            response['code'] = 1001
            response['msg'] = 'something wrong...'

        return Response(response)


"""价格与有课程效期表序列化"""
class ShopPriceJson(serializers.ModelSerializer):  # 模板
    valid_period = serializers.CharField(source='get_valid_period_display')
    class Meta:
        model = models.PricePolicy
        fields = ['valid_period','id','price']

""" 购物车API """
class Shopping(APIView):
    # obj = models.Course.objects.get(pk=1).price_policy #根据可能,或许关联的可能(多)
    # obj = models.PricePolicy.objects.get(pk=2).content_type #根据 价格与有课程效期表 找关联课程
    def __init__(self):
        self.r = SingleRedis()  #单利模式
    def get(self,request,*args,**kwargs):
        """ 获取购物车信息 """
        ######
        nid = '1'  # 用户Id 测试
        ######

        info = {'code': 200, 'msg': '', 'content': {'course':{}}} #返回的数据
        if not nid:
            info = {'code': 401, 'msg': '尚未登陆', 'content': ''}  # 状态信息
            return Response(info)
        course_list = self.r.conn.hkeys('price_user_%s'%nid)   #所有的课程对象

        try:
            for i in course_list:
                i = str(i,encoding='utf-8')
                course_obj = models.Course.objects.get(id=i)#课程对象
                default = models.PricePolicy.objects.get(pk=str(self.r.conn.hget('price_user_%s' % nid, i), encoding='utf-8')).price  # 默认价格

                info['content']['course']['%s'%course_obj.pk] = {'name':course_obj.name,'default':default,'policy':ShopPriceJson(instance=course_obj.price_policy,many=True).data}
        except:
            info = {'code': 400, 'msg': '获取数据错误', 'content': {'course': {}}}  # 返回的数据
        return Response(info)

    def post(self,request,*args,**kwargs):
        """ 增加购物车信息 """
        info = {'code':200,'msg':'','content':''}   #状态信息
        price_policy_id = request.data.get('price_policy_id') #策略ID


        ######
        nid = '1'  # 用户Id
        if price_policy_id == None: #测试
            price_policy_id = '1'   #价格与课程表id
        ######


        if not nid:
            info = {'code': 401, 'msg': '尚未登陆', 'content': ''}  # 状态信息
            return Response(info)

        try:
            obj = models.PricePolicy.objects.get(pk=price_policy_id) #课程对象
            if self.r.conn.hget('price_user_%s'%nid,str(obj.pk)):
                info = {'code': 204, 'msg': '', 'content': '更新数据'}  # 状态信息
            self.r.conn.hset('price_user_%s'%nid,obj.pk,price_policy_id)  #增加数据格式：price_user_用户id；课程id；价格与课程表id
        except:
            info = {'code': 400, 'msg': '添加出错', 'content': ''}

        return Response(info)

    def delete(self,request,*args,**kwargs):
        """ 删除购物车信息 """
        info = {'code': 200, 'msg': '', 'content': '删除数据'}  # 状态信息
        price_policy_id = request.data.get('price_policy_id') #策略id

        ######
        nid = '1'  # 用户Id
        if price_policy_id == None: #测试
            price_policy_id = '1'   #价格与课程表id
        ######

        try:
            obj = models.PricePolicy.objects.get(pk=price_policy_id)  # 课程对象
            self.r.conn.hdel('price_user_%s'%nid,obj.pk)  #删除数据
        except:
            info = {'code': 400, 'msg': '删除出错', 'content': ''}  # 状态信息
        return Response(info)

    def put(self,request,*args,**kwargs):
        """ 更新购物车信息 """
        price_policy_id = request.data.get('price_policy_id') #策略id

        ######
        nid = '1'  # 用户Id
        if price_policy_id == None: #测试
            price_policy_id = '1'   #价格与课程表id
        ######

        info = {'code': 200, 'msg': '', 'content': '更新数据'}  # 状态信息
        try:
            obj = models.PricePolicy.objects.get(pk=price_policy_id)  # 课程对象
            if self.r.conn.hget('price_user_%s' % nid, str(obj.pk)):  #数据存在,则更新操作
                self.r.conn.hset('price_user_%s' % nid, obj.pk, price_policy_id)  # 增加数据格式：price_user_用户id；课程id；价格与课程表id
            else:
                info = {'code': 410, 'msg': '数据不存在', 'content': ''}
        except:
            info = {'code': 400, 'msg': '更新出错', 'content': ''}

        return Response(info)
