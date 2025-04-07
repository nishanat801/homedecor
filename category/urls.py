from django.urls import path
from . import views

urlpatterns = [
    path('category-list/', views.category_list, name='category_list'),
    path('add-category/', views.add_category, name='add_category'),
    path('edit-category/<int:pk>/', views.edit_category, name='edit_category'),
    path('unlist/category/<int:category_id>/', views.unlist_category, name='unlist_category'),
    path('list/category/<int:category_id>/', views.list_category, name='list_category'),
]
