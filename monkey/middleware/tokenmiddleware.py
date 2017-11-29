# from django.utils.deprecation import MiddlewareMixin
#
# class ToekenMD(MiddlewareMixin):
#     def process_response(self,request,response):
#         # print('>>>>', request.COOKIE)
#         if request.method == 'OPTIONS':
#             response['Access-Control-Allow-Methods'] = "POST"  # 允许跨域访问的 请求方式
#             response['Access-Control-Allow-Origin']="http://localhost:8090"
#             response['Access-Control-Allow-Headers'] = "Content-Type"  # 允许请求头 值为 请求头的key
#             response['Access-Control-Allow-Credentials'] = "true"  #
#         else:
#             response['Access-Control-Allow-Origin'] = "http://localhost:8090"
#             response['Access-Control-Allow-Credentials'] = "true"
#         return response

class MiddlewareMixin(object):
    def __init__(self, get_response=None):
        self.get_response = get_response
        super(MiddlewareMixin, self).__init__()

    def __call__(self, request):
        response = None
        if hasattr(self, 'process_request'):
            response = self.process_request(request)
        if not response:
            response = self.get_response(request)
        if hasattr(self, 'process_response'):
            response = self.process_response(request, response)
        return response



from django.shortcuts import HttpResponse
""" CORS 解决跨域请求 """
class ToekenMD(MiddlewareMixin):
    """ CORS 解决跨域请求问题 """
    def process_request(self, request):
        """ 请求进来时候会执行的方法 """

        if request.method == 'OPTIONS':
            return HttpResponse()

    def process_response(self, request, response):
        """ 请求出去时执行方法 """
        response['Access-Control-Allow-Origin'] = "http://localhost:8090"  #允许跨域访问的网站
        response['Access-Control-Allow-Methods'] = "POST,PUT,PATCH,GET,DELETE"  # 允许跨域访问的 请求方式
        response['Access-Control-Allow-Headers'] = "Content-Type,token"  # 允许请求头 值为 请求头的key
        response['Access-Control-Allow-Credentials'] = "true"  #运行客户端携带证书式访问
        return response