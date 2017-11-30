
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


class ToekenMD(MiddlewareMixin):
    def process_response(self,request,response):
        # print('>>>>', request.COOKIE)
        if request.method == 'OPTIONS':
            response['Access-Control-Allow-Methods'] = "POST,PUT,PATCH,GET,DELETE"  # 允许跨域访问的 请求方式
            response['Access-Control-Allow-Origin']="http://localhost:8090"
            response['Access-Control-Allow-Headers'] = "Content-Type"  # 允许请求头 值为 请求头的key
            response['Access-Control-Allow-Credentials'] = "true"  #
        else:
            response['Access-Control-Allow-Origin'] = "http://localhost:8090"
            response['Access-Control-Allow-Credentials'] = "true"
        return response