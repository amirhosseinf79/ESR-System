from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import random


def paginate(page_num, obj):
    paginator = Paginator(obj, 30)
    try:
        paginated_obj = paginator.page(page_num)
    except PageNotAnInteger:
        paginated_obj = paginator.page(1)
    except EmptyPage:
        paginated_obj = paginator.page(paginator.num_pages)

    return paginated_obj


def generate_rand_string():
    _str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    rand_str = ''.join([random.choice(_str) for _ in range(15)])
    return rand_str
