from django.db import models

# Create your models here.
class Account(models.Model):
    '''用户表'''
    username = models.CharField(max_length=32,verbose_name='用户名',unique=True)
    email = models.EmailField(verbose_name='邮箱',unique=True)
    telephone = models.PositiveIntegerField(verbose_name='手机号',unique=True,blank=True,null=True)
    password = models.CharField(max_length=32,verbose_name='密码')
    # tk = models.OneToOneField('Token',blank=True,null=True)

class Token(models.Model):
    token_value = models.CharField(max_length=64,verbose_name='令牌')
    user = models.OneToOneField('Account')


class CourseCategory(models.Model):
    """课程大类, e.g 前端  后端...
    id   name
     1    后端
     2    前段
    """
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return "%s" % self.name

    class Meta:
        verbose_name = "课程大类"
        verbose_name_plural = "课程大类"

class CourseSubCategory(models.Model):
    """课程子类, e.g python linux
    ID      Name    category_id
     1     Python      1

    """
    category = models.ForeignKey("CourseCategory")
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return "%s" % self.name

    class Meta:
        verbose_name = "课程子类"
        verbose_name_plural = "课程子类"

class Course(models.Model):
    """课程"""
    name = models.CharField(max_length=128, unique=True)
    # course_img = models.CharField(max_length=255)
    sub_category = models.ForeignKey("CourseSubCategory")

    # 以后：course_type=2，必须设置degree_course=xxx
    # course_type=2，的所有课程不能单独售卖
    course_type_choices = ((0, '付费'), (1, 'VIP专享'), (2, '学位课程'))
    course_type = models.SmallIntegerField(choices=course_type_choices)
    # degree_course = models.ForeignKey("DegreeCourse", blank=True, null=True, help_text="若是学位课程，此处关联学位表")

    brief = models.TextField(verbose_name="课程概述", max_length=2048)
    level_choices = ((0, '初级'), (1, '中级'), (2, '高级'))
    level = models.SmallIntegerField(choices=level_choices, default=1)
    pub_date = models.DateField(verbose_name="发布日期", blank=True, null=True)
    period = models.PositiveIntegerField(verbose_name="建议学习周期(days)", default=7)
    order = models.IntegerField("课程顺序", help_text="从上一个课程数字往后排")
    attachment_path = models.CharField(max_length=128, verbose_name="课件路径", blank=True, null=True)
    status_choices = ((0, '上线'), (1, '下线'), (2, '预上线'))
    status = models.SmallIntegerField(choices=status_choices, default=0)
    # template_id = models.SmallIntegerField("前端模板id", default=1)
    # coupon = GenericRelation("Coupon")
    # 用于GenericForeignKey反向查询，不会生成表字段，切勿删除
    # price_policy = GenericRelation("PricePolicy")

    def __str__(self):
        return "%s(%s)" % (self.name, self.get_course_type_display())

class CourseDetail(models.Model):
    """课程详情页内容"""
    course = models.OneToOneField("Course")
    hours = models.IntegerField("课时")
    course_slogan = models.CharField(max_length=125, blank=True, null=True)
    video_brief_link = models.CharField(verbose_name='课程介绍ECC9954677D8E1079C33DC5901307461 ', max_length=255, blank=True, null=True)
    why_study = models.TextField(verbose_name="为什么学习这门课程")
    what_to_study_brief = models.TextField(verbose_name="我将学到哪些内容")
    career_improvement = models.TextField(verbose_name="此项目如何有助于我的职业生涯")
    prerequisite = models.TextField(verbose_name="课程先修要求", max_length=1024)
    recommend_courses = models.ManyToManyField("Course", related_name="recommend_by", blank=True)
    teachers = models.ManyToManyField("Teacher", verbose_name="课程讲师")

    def __str__(self):
        return "%s" % self.course

class Teacher(models.Model):
    """讲师、导师表"""
    name = models.CharField(max_length=32)
    role_choices = ((0, '讲师'), (1, '导师'))
    role = models.SmallIntegerField(choices=role_choices, default=0)
    title = models.CharField(max_length=64, verbose_name="职位、职称")
    signature = models.CharField(max_length=255, help_text="导师签名", blank=True, null=True)
    image = models.CharField(max_length=128)
    brief = models.TextField(max_length=1024)

    def __str__(self):
        return self.name