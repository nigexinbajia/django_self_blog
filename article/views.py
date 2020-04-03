from django.shortcuts import render, redirect

from django.http import HttpResponse

from .models import ArticlePost

from django.db.models import Q

from .form import ArticlePostForm

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator

from comment.models import Comment

import markdown

def article_list(request):
    search = request.GET.get('search')
    order = request.GET.get('order')
    # 用户搜索逻辑
    if search:
        article_list = ArticlePost.objects.filter(
            Q(title__icontains=search)|
            Q(body__icontains=search)
        )
    else:
        search = ''
        article_list = ArticlePost.objects.all()
    
    # 热度排序
    if order == "total_views":
        article_list = article_list.order_by("-total_views")
        
    paginator = Paginator(article_list, 3)
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    context = {'articles':articles, 'order':order, 'search':search}
    return render(request, 'article/list.html', context)

def article_detail(request, id):
    article = ArticlePost.objects.get(id=id)
    comments = Comment.objects.filter(article=id)
    if article.author != request.user:
        # 浏览量+1
        article.total_views += 1
        article.save(update_fields=["total_views"])

    md = markdown.Markdown(
        extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            # 目录扩展
            'markdown.extensions.toc',
            ]
        )
    article.body = md.convert(article.body)
    context = {'article':article, 'toc':md.toc, 'comments':comments}
    return render(request, 'article/detail.html', context)

# 写文章的视图
@login_required(login_url='/userprofile/login/')
def article_create(request):
    # 判断用户是否提交数据
    if request.method == "POST":
        # 将提交的数据赋值到表单实例中
        article_post_form = ArticlePostForm(data=request.POST)
        # 判断提交的数据是否满足模型的需求
        if article_post_form.is_valid():
            # 保存数据，但暂时不提交到数据库中
            new_article = article_post_form.save(commit=False)
            # 指定数据库id=1的用户为作者
            new_article.author = User.objects.get(id=request.user.id)
            new_article.save()
            return redirect("article:article_list")
        else:
            return HttpResponse("表单内容有误，请重新填写。")
    else:
        article_post_form = ArticlePostForm()
        context = { 'article_post_form': article_post_form}
        return render(request, 'article/create.html', context)

@login_required(login_url='/userprofile/login/')
def article_update(request, id):
    article = ArticlePost.objects.get(id=id)
    if article.author != request.user:
        return HttpResponse("抱歉，你无权修改这篇文章。")

    if request.method == "POST":
        article_post_form = ArticlePostForm(data=request.POST)
        if article_post_form.is_valid():
            article.title = request.POST['title']
            article.body = request.POST['body']
            article.save()
            return redirect("article:article_detail", id=id)
        else:
            return HttpResponse("表单内容有误，请重新填写。")
    else:
        article_post_form = ArticlePostForm()
        context = {'article':article, 'article_post_form':article_post_form}
        return render(request, 'article/update.html', context)

# 删除文章的视图
@login_required(login_url='/userprofile/login/')
def article_safe_delete(request, id):
    article = ArticlePost.objects.get(id=id)
    if article.author == User.objects.get(id=request.user.id):
        if request.method == "POST":
            article.delete()
            return redirect('article:article_list')
        else:
            return HttpResponse("仅允许post请求")
    else:
        return HttpResponse("你不是作者，没有删除该文章的权限。")