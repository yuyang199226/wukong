from django.utils.deprecation import MiddlewareMixin

class ToekenMD(MiddlewareMixin):
    def process_response(self,request,response):
        # print('>>>>', request.COOKIE)
        if request.method == 'OPTIONS':
            response['Access-Control-Allow-Methods'] = "POST"  # 允许跨域访问的 请求方式
            response['Access-Control-Allow-Origin']="http://127.0.0.1:8090"
            response['Access-Control-Allow-Headers'] = "Content-Type"  # 允许请求头 值为 请求头的key
            response['Access-Control-Allow-Credentials'] = "true"  #
        else:
            response['Access-Control-Allow-Origin'] = "http://127.0.0.1:8090"
            response['Access-Control-Allow-Credentials'] = "true"
        return response