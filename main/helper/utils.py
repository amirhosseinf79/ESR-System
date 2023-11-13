from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate(page_num, obj):
    paginator = Paginator(obj, 30)
    try:
        paginated_obj = paginator.page(page_num)
    except PageNotAnInteger:
        paginated_obj = paginator.page(1)
    except EmptyPage:
        paginated_obj = paginator.page(paginator.num_pages)

    return paginated_obj
